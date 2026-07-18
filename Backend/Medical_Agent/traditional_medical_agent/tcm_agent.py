import os
import re
import json
import logging
import traceback
import time
from typing import List, Dict, Optional, Any, TypedDict, Annotated, Literal
from operator import add
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import redis
from kg_service import (
    query_kg_for_symptoms, custom_query_kg, _extract_query_target,
    search_medical_cases, search_medical_cases_by_clinical_options, get_medical_case_detail,
    search_herbs, get_herb_detail, get_formula_detail,
    search_formulas_by_effect, recommend_clinical_options,
)

load_dotenv()
logger = logging.getLogger(__name__)


SYMPTOM_NORMALIZATION_PROMPT = """你是一位专业的中医师助理，擅长从用户输入中准确提取症状、舌象和脉象信息。

【核心任务】
从用户输入和对话历史中，准确提取并区分以下三类信息：
1. 症状：患者的主观不适感觉（如头痛、咳嗽、发热等）
2. 舌象：舌头的颜色、舌苔、形态等（如舌红、舌苔薄白、舌胖等）
3. 脉象：脉搏的特征（如脉浮、脉数、脉细、脉弦、脉缓、脉滑、脉有力、脉弱等）

【识别规则】
- 舌象关键词：舌、舌苔、舌质、舌色、舌体、舌形、舌态、舌红、舌淡、舌紫、舌苔白、舌苔黄等
- 脉象关键词：脉、脉象、脉搏、脉浮、脉数、脉细、脉弦、脉缓、脉滑、脉有力、脉弱、平滑、浮紧、沉迟、洪大等
- 即使输入非常简短（如"脉象平滑"、"舌头发红"），也要准确识别并归类

【标准化规则】
1. 口语化术语 → 标准中医术语
   - "发寒"、"怕冷"、"畏寒"、"冷得发抖" → "恶寒"
   - "没汗"、"不出汗"、"身上没汗" → "无汗"
   - "头疼" → "头痛"
   - "身体疼"、"全身疼" → "身疼"
   - "骨头疼"、"关节疼" → "骨节疼痛"
   - "腰酸"、"腰疼" → "腰痛"
   - "发烧"、"发低烧" → "发热"
   - "气短"、"喘气" → "气喘"
   - "咳痰"、"有痰" → "咳嗽"（或保留"痰多"）
   - "流鼻涕"、"清涕" → "鼻流清涕"
   - "拉肚子" → "腹泻"
   - "胃疼" → "胃痛"
   - "反酸"、"烧心" → "反酸"
   - "睡不着" → "失眠"
   - "心慌" → "心悸"
   - "没胃口"、"食欲差" → "纳呆"
   - "小便黄" → "小便黄赤"
   - "手脚凉" → "手足不温"
   - "盗汗"、"夜里出汗" → "盗汗"
   - "自汗"、"白天出汗" → "自汗"

2. 提取用户描述的所有症状（不要漏掉）
3. 保留患者提到的所有体征细节（如"舌苔薄白"、"脉象浮紧"）
4. 主诉 = 用户最关注的不适
5. 判断用户是否表示无法或不愿继续提供更多信息

【用户拒绝/结束表达识别 - 重要】
当用户输入以下类型内容时，user_refused 设为 true：
- "没有了"、"没别的了"、"就这些"、"没有更多"、"没有更多可说的"
- "我不会测"、"不会测脉象"、"不会看舌象"、"不懂怎么测"、"不知道怎么测"
- "算了吧"、"就这样吧"、"不麻烦了"、"不用了"、"直接分析吧"、"直接判断吧"
- "我测不了"、"测不了脉"、"不方便"、"没条件"
- 任何明确表示无法继续补充信息的表达

【输出字段】
- symptoms: 标准化后的症状列表
- tongue: 舌象描述（原文保留）
- pulse: 脉象描述（原文保留）
- chief_complaint: 主诉（标准化后）
- is_complete: 是否包含症状+舌象+脉象
- missing_info: 缺什么
- user_refused: 用户是否表示无法或不愿继续提供更多信息（true/false）"""


class SupervisorDecision(BaseModel):
    intent: Literal["diagnosis", "ask", "custom_query", "medical_case", "explain", "greeting", "irrelevant", "done", "department_inquiry"] = Field(description="意图分类：diagnosis=诊断, ask=追问, custom_query=自定义查询, medical_case=医案检索, explain=解释原因, greeting=问候, irrelevant=无关内容, done=完成, department_inquiry=用户询问挂号/推荐科室")
    ask_question: Optional[str] = Field(default=None, description="如果intent=ask，追问的问题")
    query_target: Optional[str] = Field(default=None, description="如果intent=custom_query，查询目标")
    user_explicit_stop: bool = Field(default=False, description="用户是否明确表示不想再补充信息、希望直接进行分析判断（如'直接判断''帮我分析''不用说了''到此为止'）")
    user_refused: bool = Field(default=False, description="用户是否委婉表示无法或不愿提供更多信息（如'不知道''没有细节''不会描述''没别的了'）")
    force_diagnosis: bool = Field(default=False, description="是否应强制进入诊断流程（用户明确要求诊断或连续拒绝提供信息）")


class SymptomsInfo(BaseModel):
    symptoms: List[str] = Field(description="用户描述的症状列表")
    tongue: Optional[str] = Field(description="舌象描述")
    pulse: Optional[str] = Field(description="脉象描述")
    chief_complaint: Optional[str] = Field(description="主诉")
    is_complete: bool = Field(description="症状信息是否足够完整")
    missing_info: Optional[str] = Field(description="缺失的信息")
    user_refused: bool = Field(default=False, description="用户是否表示无法或不愿继续提供更多信息")


class RedisSessionStore:
    """带 TTL 的 Redis 会话存储，避免进程重启或跨病例串话。"""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = redis.Redis.from_url(
                os.environ["REDIS_URL"], decode_responses=True, socket_connect_timeout=2
            )
        return self._client

    @staticmethod
    def _encode(value):
        if isinstance(value, BaseMessage):
            return {"__kind__": "message", "type": value.type, "content": value.content}
        if isinstance(value, SymptomsInfo):
            return {"__kind__": "symptoms", "data": value.model_dump()}
        if isinstance(value, DiagnosisResult):
            return {"__kind__": "diagnosis", "data": value.model_dump()}
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return {str(key): RedisSessionStore._encode(item) for key, item in value.items()}
        if isinstance(value, list):
            return [RedisSessionStore._encode(item) for item in value]
        return value

    @staticmethod
    def _decode(value):
        if isinstance(value, list):
            return [RedisSessionStore._decode(item) for item in value]
        if not isinstance(value, dict):
            return value
        if value.get("__kind__") == "message":
            message_cls = HumanMessage if value.get("type") == "human" else AIMessage
            return message_cls(content=value.get("content", ""))
        if value.get("__kind__") == "symptoms":
            return SymptomsInfo(**value["data"])
        if value.get("__kind__") == "diagnosis":
            return DiagnosisResult(**value["data"])
        return {key: RedisSessionStore._decode(item) for key, item in value.items()}

    def get(self, key: str, default=None):
        raw = self.client.get(f"agent:session:{key}")
        return self._decode(json.loads(raw)) if raw else default

    def __setitem__(self, key: str, value: dict):
        self.client.setex(
            f"agent:session:{key}", self.ttl_seconds,
            json.dumps(self._encode(value), ensure_ascii=False, default=str),
        )


class DiagnosisResult(BaseModel):
    syndrome: str = Field(description="证型名称")
    treatment_principle: Optional[str] = Field(description="治法")
    therapy: Optional[str] = Field(description="用法用量")
    precautions: Optional[str] = Field(description="注意事项")
    prescription: str = Field(description="方剂名称")
    ingredients: List[str] = Field(description="药材列表")
    department: str = Field(description="推荐科室")
    allergy_warnings: Optional[List[str]] = Field(description="过敏药材警告")
    kg_warning: Optional[str] = Field(description="知识图谱安全提示")


class AgentState(TypedDict):
    session_id: str
    patient_id: str
    user_input: str
    mode: str
    scene: str
    messages: Annotated[List[BaseMessage], add]
    intent: Optional[str]
    ask_question: Optional[str]
    query_target: Optional[str]
    symptoms_info: Optional[SymptomsInfo]
    kg_raw_result: Optional[Dict[str, Any]]
    diagnosis_result: Optional[DiagnosisResult]
    patient_profile: Optional[Dict[str, Any]]
    allergy_herbs: List[str]
    final_response: Optional[str]
    ask_round: int
    refuse_count: int
    force_diagnosis: bool
    department_hint: Optional[str]


_llm_32b = None
_llm_32b_streaming = None


def _get_llm_32b() -> ChatTongyi:
    global _llm_32b
    if _llm_32b is None:
        _llm_32b = ChatTongyi(
            model_name=os.getenv("LLM_MODEL_32B"),
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
            temperature=0.1,
        )
    return _llm_32b


def _get_llm_32b_streaming() -> ChatTongyi:
    global _llm_32b_streaming
    if _llm_32b_streaming is None:
        _llm_32b_streaming = ChatTongyi(
            model_name=os.getenv("LLM_MODEL_32B"),
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
            temperature=0.1,
            streaming=True,
        )
    return _llm_32b_streaming


def _escape_braces(text: str) -> str:
    if text is None:
        return ""
    return str(text).replace("{", "{{").replace("}", "}}")


def _supervisor_decide(scene: str, mode: str, user_input: str, symptoms_info: Optional[SymptomsInfo], history_str: str) -> SupervisorDecision:
    """Supervisor: 单次 LLM 调用，判断意图"""

    known_info = ""
    if symptoms_info:
        known_parts = []
        if symptoms_info.symptoms:
            known_parts.append(f"症状：{', '.join(symptoms_info.symptoms)}")
        if symptoms_info.tongue:
            known_parts.append(f"舌象：{symptoms_info.tongue}")
        if symptoms_info.pulse:
            known_parts.append(f"脉象：{symptoms_info.pulse}")
        if known_parts:
            known_info = "\n【已知信息】当前已收集：\n" + "\n".join(known_parts) + "\n\n"

    if scene == "guide":
        system_prompt = """你是中医药问诊系统的Supervisor，负责判断用户意图并调度。

【可用意图】
- diagnosis: 症状信息已足够（包含症状+舌象+脉象），进行完整诊断
- explain: 用户追问原因或要求解释（如"为什么"、"为什么挂神经内科"），基于已有信息给出解释
- ask: 症状信息不完整，需要追问用户补充信息（注意：仅当用户在描述自己的病情但信息不全时使用）
- custom_query: 用户主动查询中医药知识（如"麻黄的功效""舌象脉象怎么测""什么是脾胃虚弱""桂枝汤的配伍"等知识性、方法性问题）。当用户询问的是中医概念、测量方法、药材功效等知识性问题，而不是在描述自己的症状时，应识别为custom_query
- medical_case: 用户想查看医案
- department_inquiry: 用户询问挂号建议、推荐科室（如"我应该挂什么科""挂什么号""看什么科""应该挂哪个科室"），需要基于已有症状推荐合适的就诊科室
- greeting: 用户发送问候语（如"你好"、"您好"、"在吗"），需要友好回应并介绍系统功能
- irrelevant: 用户输入与中医药问诊完全无关的内容（如天气、股票、娱乐等），需要友好说明系统定位
- done: 当前对话已完成，无需进一步处理

【挂号/科室咨询识别 - 非常重要】
当用户询问以下内容时，识别为 department_inquiry：
- "我应该挂什么科""挂什么号""看什么科""挂哪个科室""应该看什么科"
- "去医院看什么科""这个病挂什么科""需要挂什么科"
- "挂什么科的号""推荐科室""应该去哪个科室"
- 即使用户同时说了"不方便提供"等信息，只要包含挂号/科室咨询，都应识别为 department_inquiry
判断时需理解用户真实意图，不要硬编码关键词匹配。

【科室推断参考】
- 风寒、风热、恶寒、感冒、咳嗽、哮喘、肺炎、发热 → 呼吸内科/中医内科
- 头痛、眩晕、头晕、失眠 → 神经内科/中医内科
- 心悸、胸痹、心痛、高血压、冠心病 → 心血管内科
- 胃痛、胃炎、腹泻、便秘、腹痛、消化不良、黄疸、胁痛 → 消化内科
- 腰痛、痹证、关节炎、颈椎 → 骨伤科
- 月经、痛经、带下、不孕 → 妇科
- 小儿、儿科相关症状 → 儿科
- 湿疹、荨麻疹、皮炎、瘙痒、银屑病 → 皮肤科
- 肾、水肿 → 肾病科/中医内科
- 前列腺、尿路 → 泌尿外科
- 糖尿病、甲亢 → 内分泌科
- 肝郁、气虚、血虚、阴虚、阳虚、湿热、痰湿、血瘀 → 中医内科

【追问原则 - 重要】
- 只追问缺失的信息，不要重复已知内容
- 如果患者只说了症状（如头痛、发热），询问："请问还有哪些不适？比如怕冷还是怕热？有没有出汗？"
- 如果已问过但用户没有提供，继续追问缺失的关键信息（舌象、脉象），直到收集完整或用户明确拒绝
- 如果用户输入"无"、"没有"、"没事"等空内容：友好问候并询问用户有什么健康问题要咨询
- 如果对话历史中已经收集了部分信息，要记住已有的信息，不要重复追问
- 追问轮次限制：最多追问3次，如果用户连续2次拒绝或表示无法提供信息（如"不会测"、"不方便"、"没有其他不适"），则基于现有信息给出初步建议，不再继续追问
- 核心目标：必须收集完整的症状+舌象+脉象信息后才能进行诊断

【症状示例 - 用于提示】
当用户需要提供症状信息时，请列举常见症状作为参考（注意：不要将已收集的症状再次列入示例）：
- 头痛、头晕、眩晕、失眠、多梦、健忘
- 咳嗽、咳痰、气喘、胸闷、胸痛
- 胃痛、胃胀、恶心、呕吐、腹泻、便秘
- 发热、恶寒、出汗、盗汗、乏力
- 口干、口苦、口臭、食欲不振
- 腰痛、关节痛、麻木、肿胀
- 心悸、心慌、心烦、焦虑、抑郁

【追问话术指南】
- 缺少症状时："请描述您的具体症状，例如头痛、咳嗽、发热、失眠等，这样我才能帮您进行分析。"
- 缺少舌象时："为了更准确地辨证，请在自然光下，对镜伸舌，观察舌色、舌苔、形态，描述您看到的即可，例如舌红、舌苔厚腻等。"
- 缺少脉象时："为了更准确地辨证，请自己或找家人帮忙摸脉，描述大概感受，例如跳得快还是慢？轻按就有还是重按才摸到？"
- 已收集部分信息时："已了解您的症状，还需要您提供舌象和脉象信息，这样才能做出准确的诊断。"
- 如果用户不方便提供："如不方便提供也没关系，我可以基于已有信息给您一个初步建议，但诊断准确性会受到影响。"
- 症状信息完整时："感谢您提供的信息，我现在为您进行分析。"

【重复输入处理规则 - 非常重要】
- 如果用户重复输入了已收集的症状（如再次输入"头痛"），不要机械重复之前的追问话术
- 应当简短确认收到，然后追问尚未收集的信息
- 例如：用户已说"头痛"，再次说"头痛"时，回复："已了解您有头痛，请问还有其他不适吗？比如怕冷、出汗等情况。"
- 绝对不要与上一轮回复完全相同，每次回复要有变化

【拒绝提供信息处理规则 - 非常重要】
- 当用户表示无法或不愿提供舌象/脉象信息时（如"不方便提供""不会测""不知道""算了"等）：
  - 如果用户同时要求基于已有信息分析（如"就以目前信息""初步建议""直接判断"）：直接输出 intent=diagnosis，不再追问
  - 如果用户只是简单拒绝（如"不知道""不会测"）：也直接输出 intent=diagnosis，基于已有症状给出初步分析，不再继续追问
- 当用户表示不再提供更多症状时（如"没有其他了""就这些""没有了"）：
  - 直接基于已有症状信息进行分析，不再追问舌象脉象
- 核心原则：用户一旦明确拒绝提供任何缺失信息（舌象、脉象或更多症状），必须立即停止追问，基于已有信息给出诊断。绝对不要在用户拒绝后继续追问。

【追问识别 - 关键】
当用户输入以下内容时，识别为 explain（解释）意图，而不是继续追问症状：
- "为什么"、"为什么挂"、"为什么是"、"原因是什么"、"什么原因"
- "解释一下"、"说明一下"、"能不能解释"、"帮我分析"
- "分析一下"、"帮我看看"、"给我建议"、"有什么建议"

【问候与无关内容识别 - 非常重要】
- 用户输入"你好"、"您好"、"在吗"、"哈喽"、"嗨"等纯问候语：greeting
- 用户输入"今天天气怎么样"、"股票怎么卖"、"有什么好看的电影"等与中医药完全无关的内容：irrelevant
- 如果用户问候后继续问健康问题（如"你好，我最近头痛"）：不要识别为 greeting，按正常流程处理症状
- 如果用户输入模糊但可能与健康相关（如"我最近不太舒服"、"感觉有点累"）：不要识别为 irrelevant，继续追问具体症状

【问候语处理】
当识别为 greeting 时：
- 友好回应问候
- 简要介绍系统功能："我是中医药智能问诊助手，可以帮您进行症状分析、辨证论治。您可以直接告诉我您的症状，比如头痛、咳嗽、发热等。"
- 引导用户提供症状信息

【无关内容处理】
当识别为 irrelevant 时：
- 友好说明系统定位："我是中医药智能问诊系统，主要提供中医症状分析、辨证论治、中药方剂查询等服务。"
- 如果您有健康相关问题，我很乐意为您解答
- 对于完全无关的查询，礼貌地说明无法提供帮助

【规则】
- 用户问候（"你好"、"您好"、"在吗"等）：greeting
- 用户输入与中医药无关内容：irrelevant
- 患者问"人参的功效"、"麻黄汤的配伍"等：custom_query
- 患者问"有没有类似医案"、"医案"：medical_case
- 患者追问"为什么"、"为什么挂神经内科"等：explain
- 如果 symptoms_info 已存在但不完整（缺舌象/脉象）：ask，并在ask_question中明确说明还缺什么
- mode=follow-up 且无 symptoms_info：ask，并提示"请先提供症状信息"
- mode=normal 且 symptoms_info 完整（必须同时包含症状+舌象+脉象）：diagnosis
- mode=normal 且 symptoms_info 不完整（缺少舌象或脉象）：ask，继续追问缺失的信息
- 用户输入空内容（如"无"、"没有"）：ask，友好问候用户
- 患者追问原因：explain
- **重要：如果用户明确拒绝提供缺失信息，即使症状+舌象+脉象不完整，也必须输出 intent=diagnosis，基于已有信息给出诊断，绝对不要在用户拒绝后继续追问**
- 其他情况：done

【话题切换识别 - 非常重要】
- 用户可能随时切换话题，即使在之前的对话中已经提供了症状信息
- 如果当前用户输入明显是中药/方剂/医案/科普查询（如"XX有什么功效""XX是什么""XX医案"），**无论之前是否有未完成的问诊，都优先识别为 custom_query 或 medical_case**
- 不要因为他人的前一两条消息是症状描述，就把明显的中药/医案查询误判为诊断意图
- 判断依据是当前输入本身，而不是对话历史

【输出要求】
- 意图分类 + 追问问题（如果有）
- 追问问题要自然、友好，明确说明缺少什么信息
- 缺少症状时，要列举常见症状作为参考，但不要包含已收集的症状
- 不要重复询问已经收集到的信息
- 参考科室推断规则，在追问时可适当提示推荐科室
- 每次回复的话术要有变化，不要与上一轮完全相同

【用户拒绝/强制诊断判断 - 非常重要】
除了意图分类，你还需要判断以下三个布尔字段：
- user_explicit_stop：用户是否明确表示不想再补充信息、希望直接进行分析判断。包括但不限于：用户说"直接判断""帮我分析""帮我看看""到此为止""不用说了""不问了""帮我判断""直接告诉我""直接说""结束""就这样""不方便提供""就以目前信息""基于现有信息"等表达。注意：只要用户表达了"不方便提供""算了""就这些"并同时要求"基于已有信息分析""初步建议"，都应识别为明确要求结束。
- user_refused：用户是否委婉表示无法或不愿提供更多信息（但未明确要求结束）。包括但不限于：用户说"不知道""没有细节""不会描述""不清楚""没别的了""说完了""就这些了""没有要说的""不会""不懂""没有其他""没有了""没别的"等表达。注意：用户重复已有症状（如"就是胃胀食欲差"）不视为拒绝。
- force_diagnosis：是否应强制进入诊断流程。当用户明确要求诊断（user_explicit_stop=true）或已有症状且用户连续拒绝提供信息时设为true。
判断时需理解用户的真实意图，而非简单匹配关键词。例如"没有细节了"表示用户无法再提供更多信息，应设user_refused=true；"直接帮我分析吧"表示用户希望结束追问，应设user_explicit_stop=true、force_diagnosis=true。""" + known_info
    else:
        system_prompt = """你是中医临床辅助系统的Supervisor，负责判断用户意图并调度。

【可用意图】
- diagnosis: 医生提供了患者症状信息（包含症状+舌象+脉象），进行辨证
- explain: 医生追问原因或要求解释（如"为什么"、"为什么推荐这个方剂"），基于已有信息给出解释
- ask: 医生未提供足够信息，追问（如缺少舌象或脉象）（注意：仅当医生在描述患者病情但信息不全时使用）
- custom_query: 医生想查询中医药知识（如"麻黄的功效"、"麻黄汤的配伍"、"舌象脉象怎么测"、"什么是脾胃虚弱"等知识性、方法性问题）。当询问的是中医概念、测量方法、药材功效等知识性问题，而不是在描述患者症状时，应识别为custom_query
- medical_case: 医生想查询医案
- department_inquiry: 医生询问推荐科室（如"患者应该挂什么科""看什么科"），基于已有症状推荐科室
- greeting: 医生发送问候语（如"你好"、"您好"），需要友好回应并介绍系统功能
- irrelevant: 医生输入与中医临床完全无关的内容，需要友好说明系统定位
- done: 当前对话已完成

【挂号/科室咨询识别 - 非常重要】
当用户询问挂号建议、推荐科室时（如"挂什么科""看什么科""应该挂哪个科室"），识别为 department_inquiry。
判断时需理解用户真实意图，不要硬编码关键词匹配。

【科室推断参考】
- 风寒、风热、恶寒、感冒、咳嗽、哮喘、肺炎、发热 → 呼吸内科/中医内科
- 头痛、眩晕、头晕、失眠 → 神经内科/中医内科
- 心悸、胸痹、心痛、高血压、冠心病 → 心血管内科
- 胃痛、胃炎、腹泻、便秘、腹痛、消化不良、黄疸、胁痛 → 消化内科
- 腰痛、痹证、关节炎、颈椎 → 骨伤科
- 月经、痛经、带下、不孕 → 妇科
- 小儿、儿科相关症状 → 儿科
- 湿疹、荨麻疹、皮炎、瘙痒、银屑病 → 皮肤科
- 肾、水肿 → 肾病科/中医内科
- 前列腺、尿路 → 泌尿外科
- 糖尿病、甲亢 → 内分泌科
- 肝郁、气虚、血虚、阴虚、阳虚、湿热、痰湿、血瘀 → 中医内科

【追问原则 - 重要】
- 只追问缺失的关键信息（舌象或脉象）
- 不要重复问已知信息
- 如果医生只提供了症状和舌象，缺少脉象，追问脉象
- 如果医生只提供了舌象，缺少症状和脉象，先问症状
- 如果医生只提供了脉象，缺少症状和舌象，先问症状
- 如果医生输入"无"、"没有"等空内容，友好问候并询问医生需要什么帮助
- 如果已问过但用户没有提供，继续追问缺失的关键信息（舌象、脉象），直到收集完整或用户明确拒绝
- 核心目标：必须收集完整的症状+舌象+脉象信息后才能进行辨证分析

【症状示例 - 用于提示】
当医生需要提供症状信息时，请列举常见症状作为参考（注意：不要将已收集的症状再次列入示例）：
- 头痛、头晕、眩晕、失眠、多梦、健忘
- 咳嗽、咳痰、气喘、胸闷、胸痛
- 胃痛、胃胀、恶心、呕吐、腹泻、便秘
- 发热、恶寒、出汗、盗汗、乏力
- 口干、口苦、口臭、食欲不振
- 腰痛、关节痛、麻木、肿胀
- 心悸、心慌、心烦、焦虑、抑郁

【追问话术指南】
- 缺少症状时："请提供患者的具体症状，例如头痛、咳嗽、发热、失眠等，这样我才能帮您进行辨证分析。"
- 缺少舌象时："为了准确辨证，请提供患者的舌象信息，例如舌红、舌淡、舌苔厚腻、舌苔黄等。"
- 缺少脉象时："为了准确辨证，请提供患者的脉象信息，例如脉浮、脉数、脉细、脉弦等。"
- 已收集部分信息时："已了解，还需要您提供患者的舌象和脉象信息，这样才能做出准确的辨证。"
- 症状信息完整时："感谢您提供的信息，我现在为您进行辨证分析。"

【重复输入处理规则 - 非常重要】
- 如果医生重复输入了已收集的症状（如再次输入"头痛"），不要机械重复之前的追问话术
- 应当简短确认收到，然后追问尚未收集的信息
- 例如：医生已说"头痛"，再次说"头痛"时，回复："已了解患者有头痛，请问还需要补充其他症状吗？或者提供舌象信息？"
- 绝对不要与上一轮回复完全相同，每次回复要有变化
- 在追问示例中不要包含已收集的症状

【追问识别 - 关键】
当医生输入以下内容时，识别为 explain（解释）意图，而不是继续追问症状：
- "为什么"、"为什么推荐"、"为什么用"、"原因是什么"、"什么原因"
- "解释一下"、"说明一下"、"能不能解释"、"帮我分析"
- "分析一下"、"帮我看看"、"给我建议"、"有什么建议"

【问候与无关内容识别 - 非常重要】
- 医生输入"你好"、"您好"、"在吗"等问候语：greeting
- 医生输入与中医临床完全无关的内容：irrelevant
- 如果医生问候后继续问临床问题（如"你好，患者头痛"）：不要识别为 greeting，按正常流程处理

【问候语处理】
当识别为 greeting 时：
- 友好回应问候
- 简要介绍系统功能："您好！我是中医临床辅助系统，可以帮您进行辨证论治、查询中药方剂和医案。请提供患者症状信息，我来协助您诊断。"

【无关内容处理】
当识别为 irrelevant 时：
- 友好说明系统定位："我是中医临床辅助系统，主要提供辨证论治、中药方剂查询、医案检索等服务。"
- 对于完全无关的查询，礼貌地说明无法提供帮助

【规则】
- 医生问候（"你好"、"您好"等）：greeting
- 医生输入与中医临床无关内容：irrelevant
- 医生问"麻黄汤的方义"、"川芎的功效"等：custom_query
- 医生问"类似医案"、"有没有医案"：medical_case
- 医生追问"为什么"、"为什么推荐这个方剂"等：explain
- 症状信息完整（必须同时包含症状+舌象+脉象）：diagnosis
- mode=follow-up 且无 symptoms_info：ask，并提示"请先提供症状信息"
- 症状信息不完整（缺少舌象或脉象）：ask，根据缺失内容选择合适的追问话术
- 医生输入空内容（如"无"、"没有"）：ask，友好问候用户
- 如果对话历史中已经收集了部分信息，要记住已有的信息，不要重复追问
- 医生追问原因：explain
- **重要：在未收集到完整的症状+舌象+脉象之前，不要提前输出 diagnosis，但如果医生明确表示不想补充更多信息，则直接进行辨证**
- 其他情况：done

【话题切换识别 - 非常重要】
- 医生可能随时切换话题，即使在之前的对话中已经提供了症状信息
- 如果当前输入明显是中药/方剂/医案/科普查询（如"XX有什么功效""XX是什么""XX医案"），**无论之前是否有未完成的辨证，都优先识别为 custom_query 或 medical_case**
- 不要因为前几条消息是症状描述，就把明显的中药/医案查询误判为诊断意图
- 判断依据是当前输入本身，而不是对话历史

【输出要求】
- 意图分类 + 追问问题（如果有）
- 追问问题要专业、明确，指出缺少什么临床信息
- 缺少症状时，要列举常见症状作为参考，但不要包含已收集的症状
- 不要重复询问已经收集到的信息
- 参考科室推断规则
- 每次回复的话术要有变化，不要与上一轮完全相同

【用户拒绝/强制诊断判断 - 非常重要】
除了意图分类，你还需要判断以下三个布尔字段：
- user_explicit_stop：用户是否明确表示不想再补充信息、希望直接进行分析判断。包括但不限于：用户说"直接判断""帮我分析""帮我看看""到此为止""不用说了""不问了""帮我判断""直接告诉我""直接说""结束""就这样""不方便提供""就以目前信息""基于现有信息"等表达。注意：只要用户表达了"不方便提供""算了""就这些"并同时要求"基于已有信息分析""初步建议"，都应识别为明确要求结束。
- user_refused：用户是否委婉表示无法或不愿提供更多信息（但未明确要求结束）。包括但不限于：用户说"不知道""没有细节""不会描述""不清楚""没别的了""说完了""就这些了""没有要说的""不会""不懂""没有其他""没有了""没别的"等表达。注意：用户重复已有症状不视为拒绝。
- force_diagnosis：是否应强制进入诊断流程。当用户明确要求诊断（user_explicit_stop=true）或已有症状且用户连续拒绝提供信息时设为true。
判断时需理解用户的真实意图，而非简单匹配关键词。""" + known_info

    symptoms_str = "无"
    if symptoms_info:
        symptoms_str = f"症状={symptoms_info.symptoms}, 舌象={symptoms_info.tongue or '无'}, 脉象={symptoms_info.pulse or '无'}"

    if len(history_str) > 2000:
        history_str = history_str[-2000:]

    human_msg = f"对话历史：\n{history_str}\n\n当前用户输入：{_escape_braces(user_input)}\n\n场景={scene}, 模式={mode}\n当前症状信息：{symptoms_str}\n\n请输出意图判断。"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_msg)
    ])

    structured_llm = _get_llm_32b().with_structured_output(SupervisorDecision)
    chain = prompt | structured_llm
    return chain.invoke({})


def _extract_symptoms_llm(user_input: str, history_str: str) -> SymptomsInfo:
    """从用户输入中提取症状信息（单次 LLM 调用，含症状标准化）"""

    user_input_escaped = _escape_braces(user_input)

    if len(history_str) > 2000:
        history_str = history_str[-2000:]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYMPTOM_NORMALIZATION_PROMPT),
        ("human", f"对话历史：\n{_escape_braces(history_str)}\n\n当前输入：{user_input_escaped}\n\n请提取并标准化症状信息。")
    ])

    structured_llm = _get_llm_32b().with_structured_output(SymptomsInfo)
    chain = prompt | structured_llm
    return chain.invoke({})


def _diagnose_and_respond(
    symptoms: List[str],
    tongue: Optional[str],
    pulse: Optional[str],
    allergy_herbs: List[str],
    scene: str,
    user_input: str,
    mode: str,
) -> tuple:
    """诊断 + 回复：单次 LLM 调用完成症状标准化、KG查询、科室判断、回复生成"""

    symptoms = symptoms[:5]

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 知识图谱查询 ======")
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 查询症状: {symptoms}")

    start_time = time.time()
    kg_result = query_kg_for_symptoms(symptoms, allergy_herbs)
    kg_time = time.time() - start_time
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 知识图谱查询完成, 耗时={kg_time:.2f}秒")

    kg_raw_result = kg_result.get("raw", {})

    prescription_list = kg_result.get("prescription", [])
    zheng_list = kg_result.get("zheng", [])
    herbs_list = kg_result.get("herbs", [])
    warnings_list = kg_result.get("warnings", [])

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] KG结果: prescriptions={len(prescription_list)}, zheng={len(zheng_list)}, herbs={len(herbs_list)}")

    safe_prescriptions = []
    unsafe_prescriptions = []

    for p_data in prescription_list[:5]:
        p_name = p_data.get("prescription", "")
        p_ingredients = p_data.get("ingredients", [])
        has_allergy = False
        if allergy_herbs and p_ingredients:
            for herb in p_ingredients[:10]:
                for allergy_herb in allergy_herbs:
                    if allergy_herb in herb:
                        has_allergy = True
                        break
                if has_allergy:
                    break
        if has_allergy:
            unsafe_prescriptions.append(p_data)
        else:
            safe_prescriptions.append(p_data)

    if safe_prescriptions:
        prescription_data = safe_prescriptions[0]
        prescription_name = prescription_data.get("prescription", "未找到方剂")
        ingredients = prescription_data.get("ingredients", [])[:10]
        # 优先从知识图谱获取疗法/用法用量（usages）和注意事项（contraindications）
        kg_usages = prescription_data.get("usages", []) or []
        kg_contraindications = prescription_data.get("contraindications", []) or []
        kg_therapy = "；".join([u for u in kg_usages if u and isinstance(u, str)])
        kg_precautions = "；".join([c for c in kg_contraindications if c and isinstance(c, str)])
    elif unsafe_prescriptions:
        prescription_name = "无最佳匹配方剂"
        ingredients = []
        kg_therapy = ""
        kg_precautions = ""
    else:
        prescription_name = "未找到方剂"
        ingredients = []
        kg_therapy = ""
        kg_precautions = ""

    if not ingredients and prescription_name == "无最佳匹配方剂":
        ingredients = ["暂无匹配药材"]

    zheng_data = zheng_list[0] if zheng_list else {}
    syndrome = zheng_data.get("syndrome", "辨证不明确") if zheng_data else "辨证不明确"
    treatment_principle = zheng_data.get("treatment_principle", "") if zheng_data else ""

    all_prescriptions_info = {
        "available": [p.get("prescription", "") for p in safe_prescriptions[:3]],
        "filtered_by_allergy": [p.get("prescription", "") for p in unsafe_prescriptions[:3]],
    }

    filtered_by_allergy_from_kg = []
    if kg_raw_result.get("notRecommendedTreatmentPlans"):
        for plan in kg_raw_result["notRecommendedTreatmentPlans"][:3]:
            name = plan.get("name", "")
            labels = plan.get("labels", [])
            if name and "方剂" in labels:
                filtered_by_allergy_from_kg.append(name)

    if filtered_by_allergy_from_kg:
        all_prescriptions_info["filtered_by_allergy"] = filtered_by_allergy_from_kg

    context_parts = []
    context_parts.append(f"症状：{', '.join(symptoms[:10])}")
    if tongue:
        context_parts.append(f"舌象：{tongue}")
    if pulse:
        context_parts.append(f"脉象：{pulse}")
    context_parts.append(f"证型：{syndrome}")
    if treatment_principle:
        context_parts.append(f"治法：{treatment_principle}")

    if prescription_name == "无最佳匹配方剂" and allergy_herbs:
        context_parts.append(f"方剂：无最佳匹配方剂")
        if all_prescriptions_info["filtered_by_allergy"]:
            context_parts.append(f"可考虑的治疗方案（被过敏排除）：{'、'.join(all_prescriptions_info['filtered_by_allergy'])}")
        context_parts.append(f"原因：患者对{'、'.join(allergy_herbs)}过敏")
    else:
        context_parts.append(f"推荐方剂：{prescription_name}")
        if ingredients and ingredients != ["暂无匹配药材"]:
            context_parts.append(f"药材：{'、'.join(ingredients)}")

    if allergy_herbs:
        context_parts.append(f"过敏警告：患者对{'、'.join(allergy_herbs)}过敏")

    if scene == "guide":
        system_prompt = """你是一位温和、专业的中医健康助手，正在和一位患者进行线上问诊。

【任务】
1. 根据患者提供的症状、舌象、脉象信息，进行辨证分析
2. 基于知识图谱结果，给出通俗易懂的健康分析和调养建议
3. 推荐就诊科室（基于症状+证型）
4. 温和提醒及时就医

【对话风格】
- 像有耐心的朋友，关心对方健康
- 语气亲切温暖，让患者安心
- 避免冷冰冰的报告格式
- 不要使用"###"或"**"等Markdown格式
- 自然分段落

【饮食与调养建议 - 重要】
- 给出饮食建议时，必须明确使用"避免""不要""少吃""不吃"等否定词
- 例如："避免吃生冷、油腻、辛辣刺激的食物""不要吃冷饮和油炸食品"
- 不要出现"吃生冷油腻的食物"这种缺少否定词的语义错误
- 建议多吃温热、清淡、易消化、营养丰富的食物

【注意】
- 不要做最终医疗诊断
- 一定要在最后温和建议去医院就诊
- 语言简洁自然
- 根据实际提供的信息进行分析，如果信息完整则给出完整分析，如果信息不完整则基于已有信息给出初步分析"""
    else:
        system_prompt = """你是一位专业、可靠的中医师助理，正在协助医生进行诊疗。

【任务】
1. 根据医生提供的患者症状、舌象、脉象信息，进行辨证分析
2. 关于方剂处理：
   - 如果有"推荐方剂"：说明方义和主要药材
   - 如果"无最佳匹配方剂"：明确告诉医生并建议基于临床经验选择
   - 绝对不要推荐过敏药材
3. 给出后续诊疗建议

【对话风格】
- 像有经验的同事，专业但不刻板
- 避免使用"###"、"**"等Markdown格式
- 像当面讨论病例一样自然
- 适当使用"您"、"建议"等礼貌用语

【最关键原则】
- 过敏药材绝不能出现在推荐方剂中
- 知识图谱未找到的方剂不要自行编造
- 根据实际提供的信息进行分析，如果信息完整则给出完整分析，如果信息不完整则基于已有信息给出初步分析"""

    user_content = "\n".join(context_parts)

    if len(user_content) > 3000:
        user_content = user_content[:3000] + "\n\n（信息过长，已截断）"

    output_format = '请按以下JSON格式输出（所有字段均为字符串）:\n' + _escape_braces('{\n  "department": "推荐科室",\n  "therapy": "用法用量",\n  "precautions": "注意事项",\n  "response": "自然语言回复"\n}')

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\n" + output_format),
        ("human", _escape_braces(user_content))
    ])

    parser = JsonOutputParser()

    # 优先使用知识图谱的疗法/用法用量和注意事项，若为空则用 LLM 生成
    therapy = kg_therapy
    precautions = kg_precautions
    try:
        chain = prompt | _get_llm_32b() | parser
        result = chain.invoke({})
        department = result.get("department", "中医内科")
        if not therapy:
            therapy = result.get("therapy", "")
        if not precautions:
            precautions = result.get("precautions", "")
        response = result.get("response", "")
    except Exception as e:
        logger.debug(f"诊断+回复LLM错误: {e}")
        try:
            response_raw = _get_llm_32b().invoke(prompt.invoke({}))
            response_text = response_raw.content if hasattr(response_raw, 'content') else str(response_raw)

            import re
            dept_match = re.search(r'"department"\s*:\s*"([^"]+)"', response_text)
            if dept_match:
                department = dept_match.group(1)
            else:
                department = "中医内科"

            resp_match = re.search(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"', response_text, re.DOTALL)
            if resp_match:
                response = resp_match.group(1).replace('\\"', '"').replace('\\n', '\n')
            else:
                response = response_text
        except Exception as e2:
            logger.debug(f"备用方案也失败: {e2}")
            response_parts = []
            response_parts.append(f"根据您的症状，主要表现为{syndrome}。")
            if prescription_name == "无最佳匹配方剂":
                response_parts.append(f"知识图谱未找到合适的方剂，请医生基于自身临床经验谨慎选择。")
            elif ingredients and ingredients != ["暂无匹配药材"]:
                response_parts.append(f"推荐方剂为{prescription_name}，主要药材有{', '.join(ingredients[:6])}。")
            if allergy_herbs:
                response_parts.append(f"注意：患者对{', '.join(allergy_herbs)}过敏。")
            if scene == "guide":
                response_parts.append("建议及时前往医院就诊。")
            response = " ".join(response_parts)
            department = "中医内科"

    diagnosis_result = DiagnosisResult(
        syndrome=syndrome,
        treatment_principle=treatment_principle,
        therapy=therapy,
        precautions=precautions,
        prescription=prescription_name,
        ingredients=ingredients,
        department=department,
        allergy_warnings=allergy_herbs if allergy_herbs else None,
        kg_warning=warnings_list[0] if warnings_list else "",
    )

    kg_raw_result["all_prescriptions_info"] = all_prescriptions_info

    return diagnosis_result, kg_raw_result, response





def supervisor_node(state: AgentState) -> AgentState:
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== Supervisor 节点 ======")

    recent_messages = state["messages"][-10:] if state["messages"] else []
    history_str = "\n".join([f"{m.type}: {m.content}" for m in recent_messages])

    decision = _supervisor_decide(
        scene=state["scene"],
        mode=state["mode"],
        user_input=state["user_input"],
        symptoms_info=state.get("symptoms_info"),
        history_str=history_str,
    )

    intent = decision.intent
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Supervisor 决策: intent={intent}, query_target={decision.query_target}")
    ask_round = state.get("ask_round", 0)
    refuse_count = state.get("refuse_count", 0)

    # 代码层确定性兜底：检查用户输入是否包含挂号/科室咨询意图
    # 当 LLM 未能正确识别 department_inquiry 时，用确定性规则覆盖
    _user_input = state["user_input"]
    _dept_keywords = ["挂什么科", "挂什么号", "看什么科", "挂哪个科", "应该挂", "看什么科",
                       "挂哪科", "什么科室", "哪个科室", "推荐科室", "挂号", "应该看什么科"]
    _has_dept_inquiry = any(kw in _user_input for kw in _dept_keywords)
    if _has_dept_inquiry and intent not in ("custom_query", "medical_case"):
        intent = "department_inquiry"
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 代码兜底：检测到挂号/科室咨询，覆盖为 department_inquiry")

    # 代码层确定性兜底：检测知识性/方法性问题（如"舌象脉象怎么测""什么是脾胃虚弱"）
    # 当用户问的不是自己的症状，而是中医知识/方法时，识别为 custom_query
    _knowledge_keywords = ["怎么测", "怎么量", "怎么观察", "怎么摸", "怎么判断",
                           "是什么意思", "什么是", "什么意思", "怎么理解",
                           "怎么区分", "怎么辨别", "如何判断", "如何区分",
                           "功效是什么", "作用是什么", "有什么用"]
    _has_knowledge_query = any(kw in _user_input for kw in _knowledge_keywords)
    if _has_knowledge_query and intent == "ask" and not _has_dept_inquiry:
        intent = "custom_query"
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 代码兜底：检测到知识性/方法性问题，覆盖为 custom_query")

    # 用户拒绝/强制诊断判断交由 LLM 完成（decision.user_explicit_stop / decision.user_refused / decision.force_diagnosis）
    force_diagnosis = False
    si = state.get("symptoms_info")
    has_symptoms = si and isinstance(si, SymptomsInfo) and si.symptoms and len(si.symptoms) > 0
    user_refused = si and isinstance(si, SymptomsInfo) and si.user_refused

    # LLM 判断用户委婉拒绝时，累计拒绝次数
    if decision.user_refused:
        refuse_count += 1

    # LLM 判断用户明确拒绝或要求结束追问时，只要有症状就直接进入诊断，不再追问
    # 但如果用户同时询问挂号/科室，优先处理科室咨询
    if (decision.user_explicit_stop or decision.user_refused or decision.force_diagnosis) and intent not in ("custom_query", "medical_case", "department_inquiry"):
        if has_symptoms:
            intent = "diagnosis"
            force_diagnosis = True
            logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 用户明确拒绝/结束，直接强制诊断")

    ask_round += 1

    # 关键修复：当intent=ask时，也要提取并保存当前用户输入中的信息
    # 这样即使要追问，也能保存用户已提供的舌象脉象等信息
    updated_symptoms_info = state.get("symptoms_info")
    final_ask_question = decision.ask_question
    if intent == "ask":
        # 提取当前用户输入中的症状信息
        new_si = _extract_symptoms_llm(state["user_input"], history_str)
        existing_si = state.get("symptoms_info")

        if existing_si and isinstance(existing_si, SymptomsInfo):
            # 合并已有信息和新提取的信息
            merged_symptoms = list(set((existing_si.symptoms or []) + (new_si.symptoms or [])))
            merged_tongue = existing_si.tongue or new_si.tongue
            merged_pulse = existing_si.pulse or new_si.pulse
            merged_refused = existing_si.user_refused or new_si.user_refused

            missing_items = []
            if not merged_tongue:
                missing_items.append("舌象")
            if not merged_pulse:
                missing_items.append("脉象")
            is_complete = bool(merged_tongue and merged_pulse and len(merged_symptoms) > 0)
            missing_info = f"还需要：{'、'.join(missing_items)}" if missing_items else ""

            updated_symptoms_info = SymptomsInfo(
                symptoms=merged_symptoms,
                tongue=merged_tongue,
                pulse=merged_pulse,
                chief_complaint=new_si.chief_complaint or existing_si.chief_complaint,
                is_complete=is_complete,
                missing_info=missing_info,
                user_refused=merged_refused,
            )
            logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Supervisor提取并合并: symptoms={merged_symptoms}, tongue={merged_tongue}, pulse={merged_pulse}, is_complete={is_complete}")

            # 如果信息已完整（症状+舌象+脉象齐备），强制进入诊断
            if is_complete:
                logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 信息已完整，强制诊断")
                intent = "diagnosis"
                force_diagnosis = True

            # 如果用户已明确拒绝提供舌象脉象，且有症状，直接强制诊断
            if merged_symptoms and (decision.user_explicit_stop or decision.user_refused or merged_refused):
                logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 合并后用户已拒绝，强制诊断")
                intent = "diagnosis"
                force_diagnosis = True

            # 根据缺失信息和场景（患者端/医生端）构造明确的追问话术
            symptoms_str = "、".join(merged_symptoms[:5]) if merged_symptoms else ""
            is_doctor_scene = state.get("scene") == "doctor"

            if missing_items and not force_diagnosis:
                if is_doctor_scene:
                    # 医生端：使用专业医学语言，面向"患者"
                    ask_parts = []
                    if symptoms_str:
                        ask_parts.append(f"已了解患者有{symptoms_str}等症状。")
                    if "舌象" in missing_items and "脉象" in missing_items:
                        ask_parts.append("为了准确辨证，请补充患者的舌象和脉象信息（如舌淡红苔薄白、脉浮紧等）。")
                    elif "舌象" in missing_items:
                        ask_parts.append("为了准确辨证，请补充患者的舌象信息（如舌淡红苔薄白、舌红苔黄腻等）。")
                    elif "脉象" in missing_items:
                        ask_parts.append("为了准确辨证，请补充患者的脉象信息（如脉浮紧、脉浮数、脉弦等）。")
                    final_ask_question = "".join(ask_parts)
                else:
                    # 患者端：使用通俗易懂的语言，面向"您"
                    ask_parts = []
                    if symptoms_str:
                        ask_parts.append(f"已了解您有{symptoms_str}等症状。")
                    if "舌象" in missing_items and "脉象" in missing_items:
                        ask_parts.append("为了更准确地辨证，还需要您提供舌象和脉象信息。")
                        ask_parts.append("舌象：请在自然光下对镜伸舌，描述舌色和舌苔（如舌淡红苔薄白、舌红苔黄腻等）。")
                        ask_parts.append("脉象：请自己或请家人帮忙摸脉，描述大致感受（如跳得快还是慢、轻按还是重按才摸到等）。")
                    elif "舌象" in missing_items:
                        ask_parts.append("为了更准确地辨证，还需要您提供舌象信息。请在自然光下对镜伸舌，描述舌色和舌苔（如舌淡红苔薄白、舌红苔黄腻等）。")
                    elif "脉象" in missing_items:
                        ask_parts.append("为了更准确地辨证，还需要您提供脉象信息。请自己或请家人帮忙摸脉，描述大致感受（如跳得快还是慢、轻按还是重按才摸到等）。")
                    ask_parts.append("如不方便提供也没关系，我可以基于已有信息给您一个初步建议。")
                    final_ask_question = "".join(ask_parts)
        else:
            # 首次提取
            updated_symptoms_info = new_si
            logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Supervisor首次提取: symptoms={new_si.symptoms}, tongue={new_si.tongue}, pulse={new_si.pulse}, is_complete={new_si.is_complete}")

            # 首次提取时，如果信息已完整（症状+舌象+脉象齐备），强制进入诊断
            if new_si.is_complete:
                logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 首次提取信息已完整，强制诊断")
                intent = "diagnosis"
                force_diagnosis = True
            # 首次提取时，如果用户已明确拒绝提供舌象脉象，且有症状，直接强制诊断
            elif new_si.symptoms and (decision.user_explicit_stop or decision.user_refused or new_si.user_refused):
                logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 首次提取后用户已拒绝，强制诊断")
                intent = "diagnosis"
                force_diagnosis = True
            # 首次提问时，如果已有症状但缺舌象脉象，根据场景使用不同话术
            elif new_si.symptoms:
                symptoms_str = "、".join(new_si.symptoms[:5])
                is_doctor_scene = state.get("scene") == "doctor"
                if not new_si.tongue and not new_si.pulse:
                    if is_doctor_scene:
                        final_ask_question = (
                            f"已了解患者有{symptoms_str}等症状。为了准确辨证，请补充患者的舌象和脉象信息（如舌淡红苔薄白、脉浮紧等）。"
                        )
                    else:
                        final_ask_question = (
                            f"已了解您有{symptoms_str}等症状。为了更准确地辨证，还需要您提供舌象和脉象信息。"
                            "舌象：请在自然光下对镜伸舌，描述舌色和舌苔（如舌淡红苔薄白、舌红苔黄腻等）。"
                            "脉象：请自己或请家人帮忙摸脉，描述大致感受（如跳得快还是慢、轻按还是重按才摸到等）。"
                            "如不方便提供也没关系，我可以基于已有信息给您一个初步建议。"
                        )
                elif not new_si.tongue:
                    if is_doctor_scene:
                        final_ask_question = (
                            f"已了解患者有{symptoms_str}等症状。为了准确辨证，请补充患者的舌象信息（如舌淡红苔薄白、舌红苔黄腻等）。"
                        )
                    else:
                        final_ask_question = (
                            f"已了解您有{symptoms_str}等症状。为了更准确地辨证，还需要您提供舌象信息。"
                            "请在自然光下对镜伸舌，描述舌色和舌苔（如舌淡红苔薄白、舌红苔黄腻等）。"
                        )
                elif not new_si.pulse:
                    if is_doctor_scene:
                        final_ask_question = (
                            f"已了解患者有{symptoms_str}等症状。为了准确辨证，请补充患者的脉象信息（如脉浮紧、脉浮数、脉弦等）。"
                        )
                    else:
                        final_ask_question = (
                            f"已了解您有{symptoms_str}等症状。为了更准确地辨证，还需要您提供脉象信息。"
                            "请自己或请家人帮忙摸脉，描述大致感受（如跳得快还是慢、轻按还是重按才摸到等）。"
                        )

    # 当intent=diagnosis且已有症状信息时，提取新输入中的症状并合并
    # 解决：用户补充新症状以区分两个病时，新症状没有累加到旧列表的问题
    # 默认舌象脉象不变（保留已有），只有症状需要累加后重新查找
    if intent == "diagnosis":
        existing_si = state.get("symptoms_info")
        if existing_si and isinstance(existing_si, SymptomsInfo) and existing_si.symptoms:
            try:
                new_si = _extract_symptoms_llm(state["user_input"], history_str)
                if new_si.symptoms:
                    # 合并症状（去重累加），舌象脉象保留已有值（无则用新值）
                    merged_symptoms = list(set((existing_si.symptoms or []) + (new_si.symptoms or [])))
                    merged_tongue = existing_si.tongue or new_si.tongue
                    merged_pulse = existing_si.pulse or new_si.pulse
                    merged_refused = existing_si.user_refused or new_si.user_refused
                    missing_items = []
                    if not merged_tongue:
                        missing_items.append("舌象")
                    if not merged_pulse:
                        missing_items.append("脉象")
                    is_complete = bool(merged_tongue and merged_pulse and len(merged_symptoms) > 0)
                    missing_info = f"还需要：{'、'.join(missing_items)}" if missing_items else ""
                    updated_symptoms_info = SymptomsInfo(
                        symptoms=merged_symptoms,
                        tongue=merged_tongue,
                        pulse=merged_pulse,
                        chief_complaint=new_si.chief_complaint or existing_si.chief_complaint,
                        is_complete=is_complete,
                        missing_info=missing_info,
                        user_refused=merged_refused,
                    )
                    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 诊断前合并新症状: merged_symptoms={merged_symptoms}, tongue={merged_tongue}, pulse={merged_pulse}")
                    # 检查是否新症状导致信息完整（之前不完整但合并后完整）
                    if is_complete and not existing_si.is_complete:
                        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 合并新症状后信息完整")
            except Exception as e:
                logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 诊断前合并新症状失败: {e}")

    return {
        **state,
        "intent": intent,
        "ask_question": final_ask_question,
        "query_target": decision.query_target,
        "ask_round": ask_round,
        "refuse_count": refuse_count,
        "force_diagnosis": force_diagnosis,
        "symptoms_info": updated_symptoms_info,
        "messages": state["messages"] + [AIMessage(content=f"[Supervisor] 意图: {intent}, 追问轮次: {ask_round}, 拒绝次数: {refuse_count}, 强制诊断: {force_diagnosis}")],
    }


def extract_symptoms_node(state: AgentState) -> AgentState:
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 症状提取节点 ======")

    recent_messages = state["messages"][-10:] if state["messages"] else []
    history_str = "\n".join([f"{m.type}: {m.content}" for m in recent_messages])

    new_si = _extract_symptoms_llm(state["user_input"], history_str)

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 提取症状: symptoms={new_si.symptoms}, tongue={new_si.tongue}, pulse={new_si.pulse}, is_complete={new_si.is_complete}")

    existing_si = state.get("symptoms_info")

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 现有症状信息: existing_si={existing_si}")
    if existing_si:
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 现有: symptoms={existing_si.symptoms}, tongue={existing_si.tongue}, pulse={existing_si.pulse}")

    if existing_si and isinstance(existing_si, SymptomsInfo):
        merged_symptoms = list(set((existing_si.symptoms or []) + (new_si.symptoms or [])))
        merged_tongue = existing_si.tongue or new_si.tongue
        merged_pulse = existing_si.pulse or new_si.pulse
        merged_refused = existing_si.user_refused or new_si.user_refused

        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 合并后: symptoms={merged_symptoms}, tongue={merged_tongue}, pulse={merged_pulse}")

        missing_items = []
        if not merged_tongue:
            missing_items.append("舌象")
        if not merged_pulse:
            missing_items.append("脉象")
        is_complete = bool(merged_tongue and merged_pulse and len(merged_symptoms) > 0)
        missing_info = f"还需要：{'、'.join(missing_items)}" if missing_items else ""
        symptoms_info = SymptomsInfo(
            symptoms=merged_symptoms,
            tongue=merged_tongue,
            pulse=merged_pulse,
            chief_complaint=new_si.chief_complaint or existing_si.chief_complaint,
            is_complete=is_complete,
            missing_info=missing_info,
            user_refused=merged_refused,
        )
    else:
        symptoms_info = new_si

    msg = f"已提取症状：{symptoms_info.symptoms}, 舌象={symptoms_info.tongue}, 脉象={symptoms_info.pulse}, 完整={symptoms_info.is_complete}"

    return {
        **state,
        "symptoms_info": symptoms_info,
        "messages": state["messages"] + [AIMessage(content=msg)],
    }


def diagnosis_and_response_node(state: AgentState) -> AgentState:
    """合并：诊断 + 回复生成（单次 LLM 调用）"""

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 诊断节点 ======")

    si = state.get("symptoms_info")
    if not si or not isinstance(si, SymptomsInfo):
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 缺少症状信息")
        return {
            **state,
            "final_response": "未提供症状信息，无法进行诊断。",
            "messages": state["messages"] + [AIMessage(content="缺少症状信息")],
            "is_diagnosed": True,
        }

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始诊断: symptoms={si.symptoms}, tongue={si.tongue}, pulse={si.pulse}")

    diagnosis_result, kg_raw_result, response_text = _diagnose_and_respond(
        symptoms=si.symptoms,
        tongue=si.tongue,
        pulse=si.pulse,
        allergy_herbs=state.get("allergy_herbs", []),
        scene=state["scene"],
        user_input=state["user_input"],
        mode=state["mode"],
    )

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 诊断完成: syndrome={diagnosis_result.syndrome}, prescription={diagnosis_result.prescription}")

    return {
        **state,
        "kg_raw_result": kg_raw_result,
        "diagnosis_result": diagnosis_result,
        "final_response": response_text,
        "is_diagnosed": True,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }


def _clean_text(text: str) -> str:
    """清洗文本，去除多余标点和特殊字符"""
    if not text:
        return ""
    text = str(text).strip()
    text = text.replace("；；", "；").replace(";;", "；")
    text = text.replace("、；", "；").replace("；、", "；")
    text = text.replace("，，", "，").replace(",,", "，")
    text = text.replace("。。", "。").replace("..", "。")
    text = text.replace("；，", "，").replace(",；", "，")
    text = text.replace("；；；", "；").replace("；；；；", "；")
    text = text.replace("、、", "、").replace(",,", "、")
    text = text.replace("；\n", "；").replace("；\r", "；")
    text = text.replace("\n\n", "\n").replace("\r\r", "\r")
    text = text.replace("  ", " ").replace("   ", " ")
    if text.endswith("；") or text.endswith(",") or text.endswith("、"):
        text = text[:-1] + "。"
    return text.strip()


def _split_long_text(text: str, max_length: int = 80) -> list:
    """将长文本分割成多行，便于阅读"""
    text = _clean_text(text)
    if len(text) <= max_length:
        return [text]

    sentences = re.split(r'(；|。|！|\?)', text)
    result = []
    current_line = ""

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        punctuation = sentences[i+1] if i+1 < len(sentences) else ""

        if len(current_line) + len(sentence) + len(punctuation) <= max_length:
            current_line += sentence + punctuation
        else:
            if current_line:
                result.append(current_line.strip())
            current_line = sentence + punctuation

    if current_line:
        result.append(current_line.strip())

    return [line for line in result if line]


def _clean_field_text(text: str) -> str:
    """清洗单个字段的文本，去除严重乱序和标点问题"""
    if not text:
        return ""

    text = str(text).strip()

    text = text.replace("；；", "；").replace(";;", "；")
    text = text.replace("、；", "；").replace("；、", "；")
    text = text.replace("，，", "，").replace(",,", "，")
    text = text.replace("。。", "。").replace("..", "。")
    text = text.replace("；，", "，").replace(",；", "，")
    text = text.replace("、、", "、").replace(",,", "、")
    text = text.replace("  ", " ").replace("   ", " ")

    if text.endswith("；") or text.endswith(",") or text.endswith("、"):
        text = text[:-1] + "。"

    return text.strip()


def _format_herb_detail(herb: dict) -> str:
    """将中药详情格式化为自然、易懂的文本"""
    lines = []
    name = herb.get("name", "未知中药")
    lines.append(f"📌 {name}")

    aliases = herb.get("aliases") or herb.get("alias_text") or herb.get("alias")
    if aliases:
        aliases_str = _clean_field_text(str(aliases).strip())
        if aliases_str:
            lines.append(f"  别名：{aliases_str}")

    effect_text = _clean_field_text(herb.get("effectText") or herb.get("effect_text") or "")
    if not effect_text:
        effects = herb.get("effects") or herb.get("effect")
        if isinstance(effects, list):
            effect_text = "、".join([_clean_field_text(str(e)) for e in effects if e])
        elif effects:
            effect_text = _clean_field_text(str(effects))

    if effect_text:
        effect_lines = _split_long_text(effect_text, 60)
        for i, line in enumerate(effect_lines):
            if i == 0:
                lines.append(f"  功效：{line}")
            else:
                lines.append(f"        {line}")

    indication_text = _clean_field_text(herb.get("indicationText") or herb.get("indication_text") or "")
    if not indication_text:
        symptoms = herb.get("symptoms") or herb.get("indication")
        if isinstance(symptoms, list):
            indication_text = "、".join([_clean_field_text(str(s)) for s in symptoms if s])
        elif symptoms:
            indication_text = _clean_field_text(str(symptoms))

    if indication_text:
        indication_lines = _split_long_text(indication_text, 60)
        for i, line in enumerate(indication_lines):
            if i == 0:
                lines.append(f"  主治：{line}")
            else:
                lines.append(f"        {line}")

    usage_text = _clean_field_text(herb.get("usageText") or herb.get("usage_text") or "")
    if not usage_text:
        usage = herb.get("usage") or herb.get("dosage")
        if usage:
            usage_text = _clean_field_text(str(usage))

    if usage_text:
        usage_clean = _clean_field_text(usage_text)
        if usage_clean:
            lines.append(f"  用法：{usage_clean}")

    nature_text = _clean_field_text(herb.get("natureTasteText") or herb.get("nature_taste_text") or "")
    if not nature_text:
        natures = herb.get("natures") or herb.get("property")
        if isinstance(natures, list):
            nature_text = "、".join([_clean_field_text(str(n)) for n in natures if n])
        elif natures:
            nature_text = _clean_field_text(str(natures))

    if nature_text:
        nature_clean = _clean_field_text(nature_text)
        if nature_clean:
            lines.append(f"  性味：{nature_clean}")

    meridian_text = _clean_field_text(herb.get("meridianText") or herb.get("meridian_text") or "")
    if not meridian_text:
        meridians = herb.get("meridians") or herb.get("meridian")
        if isinstance(meridians, list):
            meridian_text = "、".join([_clean_field_text(str(m)) for m in meridians if m])
        elif meridians:
            meridian_text = _clean_field_text(str(meridians))

    if meridian_text:
        meridian_clean = _clean_field_text(meridian_text)
        if meridian_clean:
            lines.append(f"  归经：{meridian_clean}")

    category_text = _clean_field_text(herb.get("categoryText") or herb.get("category_text") or "")
    if not category_text:
        categories = herb.get("categories") or herb.get("category")
        if isinstance(categories, list):
            category_text = "、".join([_clean_field_text(str(c)) for c in categories if c])
        elif categories:
            category_text = _clean_field_text(str(categories))

    if category_text:
        category_clean = _clean_field_text(category_text)
        if category_clean:
            lines.append(f"  分类：{category_clean}")

    contraindication_text = _clean_field_text(herb.get("contraindicationText") or herb.get("contraindication_text") or "")
    if not contraindication_text:
        contraindications = herb.get("contraindications") or herb.get("contraindication")
        if isinstance(contraindications, list):
            contraindication_text = "；".join([_clean_field_text(str(c)) for c in contraindications if c])
        elif contraindications:
            contraindication_text = _clean_field_text(str(contraindications))

    if contraindication_text:
        contraindication_lines = _split_long_text(contraindication_text, 60)
        for i, line in enumerate(contraindication_lines):
            if i == 0:
                lines.append(f"  禁忌：{line}")
            else:
                lines.append(f"        {line}")

    if herb.get("pairings"):
        pairings_str = []
        for p in herb["pairings"][:5]:
            if isinstance(p, dict):
                pairings_str.append(p.get("text", "") or p.get("description", "") or p.get("name", ""))
            else:
                pairings_str.append(str(p))
        pairings_str = [_clean_field_text(p) for p in pairings_str if p]
        if pairings_str:
            pairings_clean = "; ".join(pairings_str)
            if pairings_clean:
                lines.append(f"  常用配伍：{pairings_clean}")

    related = herb.get("relatedFormulas") or herb.get("related_formulas") or herb.get("used_in_formulas") or []
    if related:
        formula_names = []
        for f in related[:5]:
            if isinstance(f, dict):
                name_val = f.get("name", "")
                if name_val:
                    formula_names.append(_clean_field_text(name_val))
            else:
                formula_names.append(_clean_field_text(str(f)))
        if formula_names:
            lines.append(f"  相关方剂：{', '.join(formula_names)}")

    source_url = herb.get("sourceUrl") or herb.get("source_url")
    if source_url:
        lines.append(f"  来源：{source_url}")

    if not effect_text and not indication_text and not contraindication_text:
        lines.append("  ⚠️ 该药在知识图谱中尚未完善详细信息，仅有关联方剂数据")

    return "\n".join(lines)


def _format_formula_detail(formula: dict) -> str:
    """将方剂详情格式化为多行文本"""
    lines = []
    name = formula.get("name", "未知方剂")
    lines.append(f"📌 {name}")

    effects = formula.get("effects", [])
    if isinstance(effects, list):
        effects_str = "、".join(effects)
    else:
        effects_str = str(effects)
    if effects_str:
        lines.append(f"  功效：{effects_str}")

    indications = formula.get("indications", [])
    if isinstance(indications, list):
        indications_str = "、".join(indications)
    else:
        indications_str = str(indications)
    if indications_str:
        lines.append(f"  主治：{indications_str}")

    symptoms = formula.get("symptoms", [])
    if isinstance(symptoms, list) and symptoms:
        lines.append(f"  适用症状：{', '.join(symptoms[:10])}")

    herbs = formula.get("herbs", [])
    if isinstance(herbs, list) and herbs:
        if isinstance(herbs[0], dict):
            herb_strs = [f"{h.get('name', '')}({h.get('dosage', '')})" for h in herbs[:8]]
            lines.append(f"  组成：{'; '.join(herb_strs)}")
        else:
            lines.append(f"  组成：{', '.join(herbs[:8])}")

    usages = formula.get("usages", [])
    if isinstance(usages, list) and usages:
        lines.append(f"  用法：{', '.join(usages[:3])}")

    contraindications = formula.get("contraindications", [])
    if isinstance(contraindications, list) and contraindications:
        lines.append(f"  禁忌：{', '.join(contraindications[:3])}")

    sources = formula.get("sources", [])
    if isinstance(sources, list) and sources:
        lines.append(f"  出处：{', '.join(sources[:2])}")

    if formula.get("sourceUrl"):
        lines.append(f"  链接：{formula['sourceUrl']}")

    return "\n".join(lines)


def _refine_kg_response(user_input: str, raw_data: dict) -> str:
    """让LLM直接从知识图谱的原始JSON数据中提取信息并整理成清晰的中药/方剂介绍"""
    if not raw_data:
        return ""

    import json
    raw_text = json.dumps(raw_data, ensure_ascii=False, indent=2)

    if len(raw_text) > 5000:
        raw_text = raw_text[:5000] + "\n\n（数据过长，已截断）"

    system_prompt = """你是中医药知识整理助手。你的任务是从知识图谱返回的原始JSON数据中提取信息，整理成清晰、规范的中医药介绍。

【输入数据特点】
输入是一个JSON对象，可能包含：
- 中药信息：名称(name)、功效(effects/effectText)、主治(symptoms/indications/indicationText)、用法(usage/usageText)、性味(natures/natureTasteText)、归经(meridians/meridianText)、禁忌(contraindications/contraindicationText)、配伍(pairings)、相关方剂(relatedFormulas)等
- 方剂信息：名称(name)、功效(effects)、主治(indications/symptoms)、组成(herbs)、用法(usages)、禁忌(contraindications)等

【整理要求】
1. 从JSON中提取所有相关信息，不要遗漏任何有效数据
2. 按照逻辑顺序重新组织信息：
   - 中药：名称→功效→主治→用法→性味→归经→禁忌→配伍→相关方剂
   - 方剂：名称→功效→主治→组成→用法→禁忌
3. 使用正确的中文标点（全角符号）
4. 删除重复内容，保留一份即可
5. 去除无用的URL链接和格式混乱的内容
6. 保持信息准确性，不遗漏关键信息
7. 使用清晰的标题和段落，便于阅读
8. 如果JSON数据中某个字段为空或无效，跳过该字段
9. 如果数据非常混乱或缺失，根据你的中医药知识，基于用户查询关键词，生成一份标准的介绍

【输出格式】
输出整理后的文本，使用Markdown格式，包含适当的标题和列表。

【示例】
输入（中药JSON）：
{
  "name": "人参",
  "effects": ["大补元气", "补脾益肺", "生津", "安神益智"],
  "symptoms": ["体虚欲脱", "肢冷脉微", "脾虚食少", "肺虚喘咳"],
  "usage": "内服：煎汤，3-9克；或入丸、散",
  "natures": ["甘", "微苦", "微温"],
  "meridians": ["脾经", "肺经", "心经"],
  "contraindications": ["实证、热证而正气不虚者忌服", "反藜芦", "畏五灵脂"]
}

输出（整理后）：
## 人参

### 功效
大补元气，补脾益肺，生津，安神益智

### 主治
体虚欲脱，肢冷脉微，脾虚食少，肺虚喘咳，津伤口渴，内热消渴，久病虚羸，惊悸失眠，阳痿宫冷

### 用法
内服：煎汤，3-9克；或入丸、散

### 性味
甘、微苦，微温

### 归经
归脾、肺、心经

### 禁忌
实证、热证而正气不虚者忌服；反藜芦；畏五灵脂
"""

    from langchain_core.messages import SystemMessage, HumanMessage

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"用户查询：{user_input}\n\n知识图谱原始数据（JSON）：\n{raw_text}\n\n请整理并优化上述内容，确保信息清晰、准确、完整：")
    ]

    response = _get_llm_32b().invoke(messages)
    refined_text = response.content if hasattr(response, 'content') else str(response)

    return refined_text


def custom_query_node(state: AgentState) -> AgentState:
    user_input = state["user_input"]

    # 知识性/方法性问题检测：如果用户问的是"怎么测""什么是""怎么区分"等知识性问题
    # 跳过知识图谱查询，直接用LLM回答
    _knowledge_indicators = ["怎么测", "怎么量", "怎么观察", "怎么摸", "怎么判断",
                             "是什么意思", "什么是", "什么意思", "怎么理解",
                             "怎么区分", "怎么辨别", "如何判断", "如何区分",
                             "功效是什么", "作用是什么", "有什么用", "怎么测舌", "怎么测脉"]
    _is_knowledge_question = any(kw in user_input for kw in _knowledge_indicators)

    if _is_knowledge_question:
        scene = state.get("scene", "guide")
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            if scene == "guide":
                sys_prompt = """你是一位温和、专业的中医健康助手。请基于你的中医药知识回答用户的问题。
- 语气亲切温暖，像朋友间交流
- 回答简洁明了，避免冗长
- 如果是方法性问题（如怎么测舌象脉象），给出具体操作指导
- 不要要求用户提供症状，直接回答问题
- 不要推荐方剂或药材，只回答用户问的问题"""
            else:
                sys_prompt = """你是一位专业的中医师助理。请基于你的中医药知识回答问题。回答专业、简洁。不要推荐方剂，只回答用户问的问题。"""

            recent_msgs = state.get("messages", [])[-6:]
            context_str = "\n".join([f"{m.type}: {m.content}" for m in recent_msgs]) if recent_msgs else ""
            human_content = f"用户问题：{user_input}\n\n对话历史：\n{context_str}" if context_str else user_input
            response = _get_llm_32b().invoke([SystemMessage(content=sys_prompt), HumanMessage(content=human_content)])
            response_text = response.content if hasattr(response, 'content') else str(response)
            return {
                **state,
                "kg_raw_result": {},
                "final_response": response_text,
                "messages": state["messages"] + [AIMessage(content=response_text)],
            }
        except Exception as e:
            logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 知识性问题LLM回答失败: {e}")

    intent_info = _extract_query_target(user_input)
    keywords = intent_info.get("keywords", [])
    query_type = intent_info.get("query_type", "unknown")
    primary_keyword = keywords[0] if keywords and isinstance(keywords, list) else user_input

    if query_type == "herb" and primary_keyword:
        result = get_herb_detail(name=primary_keyword)
        if result.get("success") and result.get("herb"):
            kg_data = result["herb"]

            # 构建知识图谱数据文本
            kg_text_parts = []
            if kg_data.get("name"):
                kg_text_parts.append(f"【中药名】{kg_data['name']}")
            if kg_data.get("effect"):
                kg_text_parts.append(f"【功效】{kg_data['effect']}")
            if kg_data.get("indication"):
                kg_text_parts.append(f"【主治】{kg_data['indication']}")
            if kg_data.get("nature") or kg_data.get("flavor"):
                nature_flavor = f"【性味】{kg_data.get('nature', '')} {kg_data.get('flavor', '')}".strip()
                kg_text_parts.append(nature_flavor)
            if kg_data.get("meridian"):
                kg_text_parts.append(f"【归经】{kg_data['meridian']}")
            if kg_data.get("contraindication"):
                kg_text_parts.append(f"【禁忌】{kg_data['contraindication']}")
            if kg_data.get("usage"):
                kg_text_parts.append(f"【用法】{kg_data['usage']}")

            kg_text = "\n\n".join(kg_text_parts) if kg_text_parts else "知识图谱中暂无详细信息"

            system_prompt = """你是一位专业的中医药知识顾问。请基于以下知识图谱数据，整理并输出中药信息。

【重要】必须基于知识图谱数据回答，不要添加知识图谱中没有的信息。

【输出格式】
## 中药名

### 功效
列出主要功效

### 主治
列出主要治疗病症

### 用法
说明常用用法用量

### 性味
说明药性和药味

### 归经
说明归经

### 禁忌
说明禁忌人群和注意事项

【注意】
- 使用清晰的标题和列表
- 整理知识图谱数据，去除冗余和混乱内容
- 如果知识图谱某字段缺失，可以标注"暂无信息"
- 不要编造知识图谱中没有的内容"""

            from langchain_core.messages import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"以下是知识图谱中的「{primary_keyword}」数据，请整理输出：\n\n{kg_text}")
            ]

            response = _get_llm_32b().invoke(messages)
            refined_text = response.content if hasattr(response, 'content') else str(response)

            return {
                **state,
                "kg_raw_result": result,
                "final_response": refined_text,
                "messages": state["messages"] + [AIMessage(content=refined_text)],
            }
        # 知识图谱中未找到该药材的详细信息
        refined_text = f"抱歉，知识图谱中暂未找到「{primary_keyword}」的详细信息。建议您咨询专业医师或查阅权威中医药文献。"

        return {
            **state,
            "kg_raw_result": result,
            "final_response": refined_text,
            "messages": state["messages"] + [AIMessage(content=refined_text)],
        }

    if query_type == "formula" and primary_keyword:
        result = get_formula_detail(name=primary_keyword)
        if result.get("success") and result.get("formula"):
            kg_data = result["formula"]

            # 构建知识图谱数据文本
            kg_text_parts = []
            if kg_data.get("name"):
                kg_text_parts.append(f"【方剂名】{kg_data['name']}")
            if kg_data.get("composition"):
                composition = kg_data['composition']
                if isinstance(composition, list):
                    kg_text_parts.append(f"【组成】{', '.join(composition)}")
                else:
                    kg_text_parts.append(f"【组成】{composition}")
            if kg_data.get("effect"):
                kg_text_parts.append(f"【功效】{kg_data['effect']}")
            if kg_data.get("indication"):
                kg_text_parts.append(f"【主治】{kg_data['indication']}")
            if kg_data.get("usage"):
                kg_text_parts.append(f"【用法】{kg_data['usage']}")
            if kg_data.get("contraindication"):
                kg_text_parts.append(f"【禁忌】{kg_data['contraindication']}")

            kg_text = "\n\n".join(kg_text_parts) if kg_text_parts else "知识图谱中暂无详细信息"

            system_prompt = """你是一位专业的中医药知识顾问。请基于以下知识图谱数据，整理并输出方剂信息。

【重要】必须基于知识图谱数据回答，不要添加知识图谱中没有的信息。

【输出格式】
## 方剂名

### 组成
列出主要药材及用量

### 功效
说明方剂功效

### 主治
说明主治病症

### 方义
简要解释方剂配伍原理（如果知识图谱没有，标注"暂无信息"）

### 用法
说明用法用量

### 禁忌
说明禁忌（如果知识图谱没有，标注"暂无信息"）

【注意】
- 使用清晰的标题和列表
- 整理知识图谱数据，去除冗余和混乱内容
- 如果知识图谱某字段缺失，可以标注"暂无信息"
- 不要编造知识图谱中没有的内容"""

            from langchain_core.messages import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"以下是知识图谱中的「{primary_keyword}」数据，请整理输出：\n\n{kg_text}")
            ]

            response = _get_llm_32b().invoke(messages)
            refined_text = response.content if hasattr(response, 'content') else str(response)

            return {
                **state,
                "kg_raw_result": result,
                "final_response": refined_text,
                "messages": state["messages"] + [AIMessage(content=refined_text)],
            }
        # 知识图谱中未找到该方剂的详细信息
        refined_text = f"抱歉，知识图谱中暂未找到「{primary_keyword}」的详细信息。建议您咨询专业医师或查阅权威中医药文献。"

        return {
            **state,
            "kg_raw_result": result,
            "final_response": refined_text,
            "messages": state["messages"] + [AIMessage(content=refined_text)],
        }

    if query_type == "syndrome" and primary_keyword:
        result = search_formulas_by_effect(primary_keyword, limit=3)
        if result.get("formulas"):
            system_prompt = """你是一位专业的中医药知识顾问。请基于你的中医药知识，介绍与以下功效相关的方剂。

【输出格式】
## 功效：xxx

### 推荐方剂
列出相关方剂及其特点

【注意】
- 使用清晰的标题和列表
- 确保信息准确、专业
"""

            from langchain_core.messages import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"请介绍与「{primary_keyword}」相关的方剂")
            ]

            response = _get_llm_32b().invoke(messages)
            refined_text = response.content if hasattr(response, 'content') else str(response)

            return {
                **state,
                "kg_raw_result": result,
                "final_response": refined_text,
                "messages": state["messages"] + [AIMessage(content=refined_text)],
            }

    if query_type in ("symptom", "unknown") and primary_keyword:
        result = recommend_clinical_options(description=user_input, limit=3)
        if result.get("formulas"):
            response_lines = [f"关于「{user_input}」的临床推荐："]
            for f in result["formulas"][:3]:
                response_lines.append(f"\n{_format_formula_detail(f)}")

            related_herbs = result.get("related_herbs", [])
            if related_herbs:
                response_lines.append(f"\n\n📚 相关中药：")
                for h in related_herbs[:5]:
                    hname = h.get("name", "未知")
                    heffect = h.get("effectText") or (", ".join(h.get("effects", [])) if h.get("effects") else "")
                    if heffect:
                        response_lines.append(f"  · {hname}：{heffect}")
                    else:
                        response_lines.append(f"  · {hname}")

            formatted_text = "\n".join(response_lines)
            refined_text = _refine_kg_response(user_input, formatted_text)

            return {
                **state,
                "kg_raw_result": result,
                "final_response": refined_text,
                "messages": state["messages"] + [AIMessage(content=refined_text)],
            }

    # 知识图谱未匹配到结果，使用LLM自身知识回答
    scene = state.get("scene", "guide")
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        if scene == "guide":
            sys_prompt = """你是一位温和、专业的中医健康助手。请基于你的中医药知识回答用户的问题。
- 语气亲切温暖，像朋友间交流
- 回答简洁明了，避免冗长
- 如果是方法性问题（如怎么测舌象脉象），给出具体操作指导
- 不要要求用户提供症状，直接回答问题"""
        else:
            sys_prompt = """你是一位专业的中医师助理。请基于你的中医药知识回答问题。回答专业、简洁。"""

        recent_msgs = state.get("messages", [])[-6:]
        context_str = "\n".join([f"{m.type}: {m.content}" for m in recent_msgs]) if recent_msgs else ""
        human_content = f"用户问题：{user_input}\n\n对话历史：\n{context_str}" if context_str else user_input
        response = _get_llm_32b().invoke([SystemMessage(content=sys_prompt), HumanMessage(content=human_content)])
        response_text = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] custom_query LLM回答失败: {e}")
        response_text = (
            f"关于「{user_input}」的相关信息，"
            f"知识图谱中暂未匹配到条目。\n\n"
            f"建议您换个查询词，例如：\n"
            f"- 中药名：「麻黄」「桂枝」「黄芪」\n"
            f"- 方剂名：「桂枝汤」「川芎茶调散」\n"
            f"- 症状描述：「头痛 发寒 无汗」\n"
            f"- 功效关键词：「止咳平喘」「清热解毒」"
        )

    return {
        **state,
        "kg_raw_result": {},
        "final_response": response_text,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }


def _format_case_summary(case: dict, index: int) -> str:
    """将原始医案数据格式化为Markdown格式的完整医案信息"""
    lines = []

    # 标题
    title = case.get("title") or case.get("formulaName") or "未知医案"
    lines.append(f"### 第{index}个：{title}")
    lines.append("")

    # 摘要（完整内容，不截断）
    summary = case.get("summary") or case.get("rawText") or ""
    if summary:
        # 如果摘要过长（超过500字），适当截断但保留完整语句
        if len(summary) > 500:
            # 找到500字附近的句号位置，保证截断在完整语句处
            cut_pos = summary[:500].rfind("。")
            if cut_pos > 200:
                summary = summary[:cut_pos + 1]
            else:
                summary = summary[:500] + "..."
        lines.append(f"**摘要：** {summary}")
        lines.append("")

    # 详细信息
    details = []
    if case.get("doctors"):
        doctors_str = '、'.join(case["doctors"][:2]) if isinstance(case["doctors"], list) else str(case["doctors"])
        details.append(f"- **医家：** {doctors_str}")
    if case.get("diseases"):
        diseases_str = '、'.join(case["diseases"][:3]) if isinstance(case["diseases"], list) else str(case["diseases"])
        details.append(f"- **病名：** {diseases_str}")
    if case.get("syndromes"):
        syndromes_str = '、'.join(case["syndromes"][:2]) if isinstance(case["syndromes"], list) else str(case["syndromes"])
        details.append(f"- **证型：** {syndromes_str}")
    if case.get("formulas"):
        formulas_str = '、'.join(case["formulas"][:3]) if isinstance(case["formulas"], list) else str(case["formulas"])
        details.append(f"- **处方：** {formulas_str}")
    if case.get("treatmentMethods"):
        methods_str = '、'.join(case["treatmentMethods"][:3]) if isinstance(case["treatmentMethods"], list) else str(case["treatmentMethods"])
        details.append(f"- **治法：** {methods_str}")
    if case.get("symptoms"):
        symptoms_str = '、'.join(case["symptoms"][:5]) if isinstance(case["symptoms"], list) else str(case["symptoms"])
        details.append(f"- **症状：** {symptoms_str}")

    if details:
        lines.extend(details)
        lines.append("")

    # 来源（Markdown链接，可直接点击）
    source_url = case.get("sourceUrl") or case.get("source_url") or ""
    if source_url:
        lines.append(f"**来源：** [点击查看原文]({source_url})")

    # ID
    case_id = case.get("caseId") or case.get("case_id") or ""
    if case_id:
        lines.append(f"**ID：** {case_id}")

    return "\n".join(lines)


def _format_formula_with_herbs(formula: dict) -> str:
    """格式化方剂信息"""
    name = formula.get("formula") or formula.get("name", "未知方剂")
    lines = [f"  · {name}"]
    if formula.get("support"):
        lines.append(f"    支持医案数：{formula['support']}")
    if formula.get("herbs") and isinstance(formula["herbs"], list):
        herbs = formula["herbs"][:8]
        herbs_str = '、'.join(h if isinstance(h, str) else (h.get("name", "") if isinstance(h, dict) else str(h)) for h in herbs)
        if herbs_str:
            lines.append(f"    组成：{herbs_str}")
    if formula.get("evidenceCases") and isinstance(formula["evidenceCases"], list):
        evidence_str = '、'.join(formula["evidenceCases"][:2])
        lines.append(f"    证据案例：{evidence_str}")
    return "\n".join(lines)


def medical_case_node(state: AgentState) -> AgentState:
    """医案检索（基于 neo4j_case 知识图谱）"""
    user_input = state["user_input"]

    intent_info = _extract_query_target(user_input)
    keywords = intent_info.get("keywords", [user_input])
    primary_keyword = keywords[0] if keywords and isinstance(keywords, list) else user_input

    case_query_type_map = {
        "formula": "formula",
        "syndrome": "syndrome",
        "disease": "disease",
        "symptom": "symptom",
        "herb": "keyword",
    }
    case_query_type = case_query_type_map.get(
        intent_info.get("query_type", "unknown"),
        "auto"
    )

    diagnosis = state.get("diagnosis_result")
    clinical_kwargs = {}
    if diagnosis:
        if hasattr(diagnosis, 'syndrome') and diagnosis.syndrome:
            clinical_kwargs["syndrome"] = diagnosis.syndrome
        if hasattr(diagnosis, 'prescription') and diagnosis.prescription:
            clinical_kwargs["formula"] = diagnosis.prescription
        if hasattr(diagnosis, 'ingredients') and diagnosis.ingredients:
            clinical_kwargs["symptoms"] = diagnosis.ingredients[:3]

    result = None
    if clinical_kwargs:
        result = search_medical_cases_by_clinical_options(
            symptoms=clinical_kwargs.get("symptoms"),
            syndrome=clinical_kwargs.get("syndrome"),
            formula=clinical_kwargs.get("formula"),
            limit=5,
        )

    if not result or not result.get("success") or not result.get("cases"):
        result = search_medical_cases(
            query=primary_keyword,
            query_type=case_query_type,
            limit=5,
        )

    cases = []
    for item in result.get("cases", []):
        if item.get("cases"):
            for c in item["cases"]:
                c.setdefault("formulaName", item.get("name", ""))
                cases.append(c)
        else:
            cases.append(item)

    cases = cases[:5]
    recommended_formulas = result.get("recommended_formulas", [])[:3]

    if case_query_type == "formula" and result.get("cases"):
        for item in result["cases"][:3]:
            if item.get("name") and item.get("herbs"):
                herbs_str = '、'.join(
                    [h.get("name", "") if isinstance(h, dict) else str(h) for h in item.get("herbs", [])[:8]]
                )
                recommended_formulas.append({
                    "formula": item["name"],
                    "herbs": [h.get("name", "") if isinstance(h, dict) else str(h) for h in item.get("herbs", [])[:10]],
                    "support": len(item.get("cases", []))
                })

    if not cases and not recommended_formulas:
        if not result.get("success"):
            response_text = (
                f"关于「{user_input}」相关的医案检索，"
                f"暂时没有检索到结果：{result.get('message', '未知错误')}\n\n"
                f"建议您：\n"
                f"1. 换个更具体的查询词（如具体的方剂名、症状、证型或病名）\n"
                f"2. 完成诊断后，系统会自动基于诊断结果检索相关参考医案"
            )
            return {
                **state,
                "kg_raw_result": result,
                "final_response": response_text,
                "messages": state["messages"] + [AIMessage(content=response_text)],
            }

    # 构建回复：基于已有症状/证型/方剂的医案检索
    # 确定检索关键词：优先使用诊断信息，其次使用用户输入
    search_desc = user_input
    if diagnosis:
        desc_parts = []
        if hasattr(diagnosis, 'syndrome') and diagnosis.syndrome:
            desc_parts.append(diagnosis.syndrome)
        if hasattr(diagnosis, 'prescription') and diagnosis.prescription:
            desc_parts.append(diagnosis.prescription)
        if desc_parts:
            search_desc = '、'.join(desc_parts)

    response_lines = [
        f"和「{search_desc}」相似的医案包括但不限于以下 {len(cases)} 个：",
        "",
        "（仅供学习、科研和辅助参考，不能替代执业医师诊疗）",
        "",
    ]

    for i, case in enumerate(cases, 1):
        response_lines.append(_format_case_summary(case, i))
        response_lines.append("")
        response_lines.append("---")
        response_lines.append("")

    # 移除最后一个分隔线
    if response_lines and response_lines[-1] == "" and len(response_lines) >= 2 and response_lines[-2] == "---":
        response_lines = response_lines[:-2]

    response_text = "\n".join(response_lines)

    return {
        **state,
        "kg_raw_result": result,
        "final_response": response_text,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }


def router(state: AgentState) -> str:
    intent = state.get("intent", "")
    si = state.get("symptoms_info")
    is_info_complete = si and isinstance(si, SymptomsInfo) and si.is_complete

    if intent == "greeting":
        return "greeting"
    if intent == "irrelevant":
        return "irrelevant"
    if intent == "department_inquiry":
        return "department_inquiry"
    if intent == "ask":
        return "ask_user"
    if intent == "diagnosis":
        if state.get("force_diagnosis", False):
            return "diagnosis_and_response"
        if is_info_complete:
            return "diagnosis_and_response"
        else:
            si_check = state.get("symptoms_info")
            if si_check and isinstance(si_check, SymptomsInfo):
                # 用户已拒绝继续提供信息，且至少有一个症状，进入诊断
                if si_check.user_refused and si_check.symptoms and len(si_check.symptoms) > 0:
                    return "diagnosis_and_response"
                if si_check.tongue and si_check.pulse and si_check.symptoms:
                    return "diagnosis_and_response"
            return "extract_symptoms"
    if intent == "explain":
        if si and isinstance(si, SymptomsInfo) and si.symptoms and len(si.symptoms) > 0:
            return "diagnosis_and_response"
        return "extract_symptoms"
    if intent == "custom_query":
        return "custom_query"
    if intent == "medical_case":
        return "medical_case"
    if intent == "done":
        return "end"

    return "end"


def greeting_node(state: AgentState) -> AgentState:
    """处理问候语，返回友好回应并介绍系统功能"""
    scene = state.get("scene", "guide")

    if scene == "guide":
        response_text = "您好！我是中医药智能问诊助手，可以帮您进行症状分析、辨证论治、中药方剂查询等服务。请告诉我您有什么不适，比如头痛、咳嗽、发热等，我来帮您分析。"
    else:
        response_text = "您好！我是中医临床辅助系统，可以帮您进行辨证论治、查询中药方剂和医案。请提供患者症状信息，我来协助您诊断。"

    return {
        **state,
        "final_response": response_text,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }


def department_inquiry_node(state: AgentState) -> AgentState:
    """处理用户挂号/科室咨询，基于已有症状由LLM推荐科室"""
    scene = state.get("scene", "guide")
    si = state.get("symptoms_info")

    # 如果还没有症状信息，先从当前用户输入中提取（处理第一轮同时提供症状+挂号咨询的情况）
    if not si or not isinstance(si, SymptomsInfo) or not si.symptoms:
        try:
            history_str = "\n".join([f"{m.type}: {m.content}" for m in state["messages"][-6:]]) if state.get("messages") else ""
            new_si = _extract_symptoms_llm(state["user_input"], history_str)
            if new_si and new_si.symptoms:
                si = new_si
                logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] department_inquiry 提取症状: {si.symptoms}")
        except Exception as e:
            logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] department_inquiry 提取症状失败: {e}")

    symptoms = si.symptoms if si and isinstance(si, SymptomsInfo) and si.symptoms else []

    # 构造已有症状信息
    info_parts = []
    if symptoms:
        info_parts.append(f"已有症状：{'、'.join(symptoms)}")
    if si and isinstance(si, SymptomsInfo):
        if si.tongue:
            info_parts.append(f"舌象：{si.tongue}")
        if si.pulse:
            info_parts.append(f"脉象：{si.pulse}")
    known_info = "\n".join(info_parts) if info_parts else "暂无已收集的症状信息"

    if scene == "guide":
        system_prompt = f"""你是一位温和、专业的中医健康助手。患者正在询问应该挂什么科室。

【已有信息】
{known_info}

【任务】
根据患者已有的症状信息，推荐最合适的就诊科室。如果有多个相关科室，列出主要的1-3个。

【对话风格】
- 语气亲切温暖
- 直接回答患者的问题，不要分析病情
- 简洁明了

【输出要求】
直接输出推荐科室及简短理由，例如：
根据您描述的胃胀、食欲差等症状，建议您挂消化内科或中医内科。这些症状主要与消化系统相关，消化内科可以进行相关检查，中医内科可以从整体调理入手。
如果没有已收集的症状信息，回复：请先告诉我您有哪些不适症状，我再为您推荐合适的科室。"""
    else:
        system_prompt = f"""你是一位专业的中医师助理。医生正在询问患者应该挂什么科室。

【已有信息】
{known_info}

【任务】
根据已有症状信息，推荐合适的就诊科室。

【输出要求】
直接输出推荐科室及简短理由，专业简洁。如果没有已收集的症状信息，提示请先提供患者症状。"""

    try:
        llm = _get_llm_32b()
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=state["user_input"])]
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] department_inquiry_node error: {e}")
        if symptoms:
            response_text = "根据您的症状，建议您到医院咨询导诊台，或挂中医内科进行进一步诊治。"
        else:
            response_text = "请先告诉我您有哪些不适症状，我再为您推荐合适的科室。"

    return {
        **state,
        "final_response": response_text,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }


def irrelevant_node(state: AgentState) -> AgentState:
    """处理无关内容，友好说明系统定位并使用大模型对话"""
    scene = state.get("scene", "guide")
    user_input = state.get("user_input", "")

    # 使用大模型自身知识进行对话，但加入系统定位的提示
    system_context = """你是中医药智能问诊系统的对话助手。当用户输入与中医药问诊无关的内容时，你需要：
1. 友好说明系统定位："我是中医药智能问诊系统，主要提供中医症状分析、辨证论治、中药方剂查询等服务。"
2. 如果用户有健康相关问题，欢迎提问
3. 对于完全无关的查询，基于你的知识进行友好对话，但要简洁礼貌

回复要求：
- 语气友好自然
- 不要过于冗长
- 如果可能，可以尝试引导用户回到健康话题"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_context),
        ("human", user_input)
    ])

    chain = prompt | _get_llm_32b()
    response = chain.invoke({})

    response_text = response.content if hasattr(response, 'content') else str(response)

    return {
        **state,
        "final_response": response_text,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("extract_symptoms", extract_symptoms_node)
    workflow.add_node("diagnosis_and_response", diagnosis_and_response_node)
    workflow.add_node("custom_query", custom_query_node)
    workflow.add_node("medical_case", medical_case_node)
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("irrelevant", irrelevant_node)
    workflow.add_node("department_inquiry", department_inquiry_node)

    workflow.set_entry_point("supervisor")

    workflow.add_edge("extract_symptoms", "supervisor")
    workflow.add_edge("diagnosis_and_response", END)
    workflow.add_edge("custom_query", END)
    workflow.add_edge("medical_case", END)
    workflow.add_edge("greeting", END)
    workflow.add_edge("irrelevant", END)
    workflow.add_edge("department_inquiry", END)

    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "ask_user": END,
            "extract_symptoms": "extract_symptoms",
            "diagnosis_and_response": "diagnosis_and_response",
            "explain": "diagnosis_and_response",
            "custom_query": "custom_query",
            "medical_case": "medical_case",
            "greeting": "greeting",
            "irrelevant": "irrelevant",
            "department_inquiry": "department_inquiry",
            "end": END,
        }
    )

    return workflow.compile()


_SESSIONS = RedisSessionStore(ttl_seconds=int(os.getenv("AGENT_SESSION_TTL_SECONDS", "3600")))


def _session_key(session_id: str, patient_id: str, scene: str) -> str:
    return f"{scene}:{patient_id}:{session_id}"


app = build_graph()


def tcm_agent_stream_chat(session_id: str, patient_id: str, user_input: str, mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None):
    """流式版本：先获取基础信息，然后逐字生成回答"""
    from langchain_core.messages import HumanMessage
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 开始流式对话 ======")
    logger.debug("agent_session_started scene=%s", scene)
    logger.debug("agent_input_received length=%s", len(user_input))
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] mode={mode}, scene={scene}")

    config = {"configurable": {"thread_id": session_id}}
    store_key = _session_key(session_id, patient_id, scene)

    allergy_herbs = []
    if patient_profile:
        allergy_info = patient_profile.get("allergy_history", {})
        if isinstance(allergy_info, dict):
            allergy_herbs = allergy_info.get("herbs", [])
        elif isinstance(allergy_info, list):
            allergy_herbs = allergy_info

    existing_state = _SESSIONS.get(store_key, {})

    if mode == "follow-up" and existing_state.get("symptoms_info"):
        preserved_symptoms = existing_state["symptoms_info"]
        preserved_diagnosis = existing_state.get("diagnosis_result")
        preserved_kg = existing_state.get("kg_raw_result")
    elif existing_state.get("symptoms_info"):
        preserved_symptoms = existing_state["symptoms_info"]
        preserved_diagnosis = existing_state.get("diagnosis_result")
        preserved_kg = existing_state.get("kg_raw_result")
    else:
        preserved_symptoms = None
        preserved_diagnosis = None
        preserved_kg = None

    preserved_messages = existing_state.get("messages", []) or []
    if not any(getattr(m, "content", None) == user_input for m in preserved_messages):
        preserved_messages = preserved_messages + [HumanMessage(content=user_input)]

    MAX_MESSAGES = 20
    if len(preserved_messages) > MAX_MESSAGES:
        preserved_messages = preserved_messages[-MAX_MESSAGES:]

    inputs = {
        "session_id": session_id,
        "patient_id": patient_id,
        "user_input": user_input,
        "mode": mode,
        "scene": scene,
        "messages": preserved_messages,
        "intent": None,
        "ask_question": None,
        "symptoms_info": preserved_symptoms,
        "kg_raw_result": preserved_kg,
        "diagnosis_result": preserved_diagnosis,
        "patient_profile": patient_profile if patient_profile else existing_state.get("patient_profile"),
        "allergy_herbs": allergy_herbs if allergy_herbs else existing_state.get("allergy_herbs", []),
        "final_response": None,
        "ask_round": existing_state.get("ask_round", 0),
        "refuse_count": existing_state.get("refuse_count", 0),
        "force_diagnosis": existing_state.get("force_diagnosis", False),
        "department_hint": existing_state.get("department_hint"),
    }

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 调用 Agent 获取基础信息 ======")

    try:
        result = app.invoke(inputs, config)
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== Agent 调用完成 ======")
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] intent={result.get('intent')}")
    except Exception as e:
        logger.exception("agent_stream_failed")
        yield f"data: {json.dumps({'code': 500, 'data': {'status': 'error', 'response': f'处理失败：{str(e)}', 'finish': False}}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    intent = result.get("intent", "")

    if intent == "ask":
        si = result.get("symptoms_info")
        default_ask = "请提供患者症状信息，我来协助您辨证分析。" if scene == "doctor" else "请描述您的症状，我来帮您分析。"
        ask_q = result.get("ask_question") or default_ask

        session_data = dict(result)
        session_data["last_access_time"] = time.time()

        is_diagnosed = result.get("is_diagnosed", False) or existing_state.get("is_diagnosed", False)
        session_data["is_diagnosed"] = is_diagnosed

        _SESSIONS[store_key] = session_data

        # 诊断完成后，如果患者提出新问题（非追问症状），用LLM正常回答
        if is_diagnosed:
            _ask_followup_keywords = ["请提供", "请补充", "还需要", "请描述", "为了", "缺少", "缺失"]
            _is_real_followup = any(kw in ask_q for kw in _ask_followup_keywords) and ask_q != default_ask
            if not _is_real_followup:
                try:
                    llm = _get_llm_32b()
                    from langchain_core.messages import SystemMessage, HumanMessage
                    if scene == "guide":
                        sys_prompt = "你是一位温和、专业的中医健康助手。患者已完成预问诊诊断，现在提出了一个问题，请基于已有上下文友好回答。如果患者问的是如何测量舌象脉象等知识性问题，请详细指导。回答简洁明了。"
                    else:
                        sys_prompt = "你是一位专业的中医师助理。请基于已有上下文回答医生的问题。"
                    recent_msgs = existing_state.get("messages", [])[-6:]
                    context_str = "\n".join([f"{m.type}: {m.content}" for m in recent_msgs]) if recent_msgs else ""
                    human_content = f"患者问题：{user_input}\n\n对话历史：\n{context_str}" if context_str else user_input
                    response = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=human_content)])
                    ask_q = response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 流式诊断后回答失败: {e}")

        # 逐字流式发送追问文本
        if ask_q:
            for char in ask_q:
                yield f"data: {json.dumps({'code': 0, 'data': {'status': 'asking', 'response': char, 'session_id': session_id, 'finish': False}}, ensure_ascii=False)}\n\n"
                time.sleep(0.01)
        # 发送元数据（symptoms_info + finish）
        yield f"data: [METADATA]\n\n"
        yield f"data: {json.dumps({'code': 0, 'data': {'status': 'asking', 'response': '', 'session_id': session_id, 'finish': False, 'symptoms_info': si.dict() if isinstance(si, SymptomsInfo) else {}}}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    if result.get("final_response"):
        diagnosis = result.get("diagnosis_result")
        session_data = dict(result)
        session_data["last_access_time"] = time.time()

        is_diagnosed = result.get("is_diagnosed", False) or existing_state.get("is_diagnosed", False)
        session_data["is_diagnosed"] = is_diagnosed

        _SESSIONS[store_key] = session_data

        status = 'query_answer' if intent in ("custom_query", "medical_case") else 'diagnosed' if diagnosis else 'done'
        finish = True if diagnosis or session_data.get("is_diagnosed") else False

        if intent in ("custom_query", "medical_case"):
            kg_data = result.get("kg_raw_result", {})
            kg_text = ""
            primary_keyword = ""

            if intent == "custom_query":
                intent_info = _extract_query_target(user_input)
                keywords = intent_info.get("keywords", [])
                primary_keyword = keywords[0] if keywords and isinstance(keywords, list) else user_input

                if isinstance(kg_data, dict):
                    if kg_data.get("herb"):
                        kd = kg_data["herb"]
                        parts = []
                        if kd.get("name"):
                            parts.append(f"【中药名】{kd['name']}")
                        if kd.get("effect"):
                            parts.append(f"【功效】{kd['effect']}")
                        if kd.get("indication"):
                            parts.append(f"【主治】{kd['indication']}")
                        if kd.get("nature") or kd.get("flavor"):
                            parts.append(f"【性味】{kd.get('nature', '')} {kd.get('flavor', '')}".strip())
                        if kd.get("meridian"):
                            parts.append(f"【归经】{kd['meridian']}")
                        if kd.get("contraindication"):
                            parts.append(f"【禁忌】{kd['contraindication']}")
                        if kd.get("usage"):
                            parts.append(f"【用法】{kd['usage']}")
                        kg_text = "\n\n".join(parts)
                    elif kg_data.get("formula"):
                        kd = kg_data["formula"]
                        parts = []
                        if kd.get("name"):
                            parts.append(f"【方剂名】{kd['name']}")
                        if kd.get("composition"):
                            composition = kd['composition']
                            if isinstance(composition, list):
                                parts.append(f"【组成】{', '.join(composition)}")
                            else:
                                parts.append(f"【组成】{composition}")
                        if kd.get("effect"):
                            parts.append(f"【功效】{kd['effect']}")
                        if kd.get("indication"):
                            parts.append(f"【主治】{kd['indication']}")
                        if kd.get("usage"):
                            parts.append(f"【用法】{kd['usage']}")
                        if kd.get("contraindication"):
                            parts.append(f"【禁忌】{kd['contraindication']}")
                        kg_text = "\n\n".join(parts)

            if kg_text:
                system_prompt = """你是一位专业的中医药知识顾问。请基于以下知识图谱数据，整理并输出信息。

【重要】必须基于知识图谱数据回答，不要添加知识图谱中没有的信息。

【输出格式】
## 名称

### 功效
列出主要功效

### 主治
列出主要治疗病症

### 用法
说明常用用法用量

### 性味
说明药性和药味

### 归经
说明归经

### 禁忌
说明禁忌人群和注意事项

【注意】
- 使用清晰的标题和列表
- 整理知识图谱数据，去除冗余和混乱内容
- 如果知识图谱某字段缺失，可以标注"暂无信息"
- 不要编造知识图谱中没有的内容"""

                from langchain_core.messages import SystemMessage, HumanMessage

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"以下是知识图谱中的「{primary_keyword}」数据，请整理输出：\n\n{kg_text}")
                ]

                llm = _get_llm_32b_streaming()
                accumulated_text = ""
                for chunk in llm.stream(messages):
                    content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    if content:
                        accumulated_text += content
                        yield f"data: {json.dumps({'code': 0, 'data': {'status': status, 'response': content, 'session_id': session_id, 'finish': False}}, ensure_ascii=False)}\n\n"
                        time.sleep(0.02)

                yield f"data: [METADATA]\n\n"
                yield f"data: {json.dumps({'code': 0, 'data': {'status': status, 'response': '', 'session_id': session_id, 'finish': finish}}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            else:
                response_text = result["final_response"]
                # 代码层逐字切分流式发送，不依赖LLM流式行为
                if response_text:
                    for char in response_text:
                        yield f"data: {json.dumps({'code': 0, 'data': {'status': status, 'response': char, 'session_id': session_id, 'finish': False}}, ensure_ascii=False)}\n\n"
                        time.sleep(0.01)
                yield f"data: [METADATA]\n\n"
                yield f"data: {json.dumps({'code': 0, 'data': {'status': status, 'response': '', 'session_id': session_id, 'finish': finish}}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
        else:
            response_text = result["final_response"]
            # 代码层逐字切分流式发送，不依赖LLM流式行为
            if response_text:
                for char in response_text:
                    yield f"data: {json.dumps({'code': 0, 'data': {'status': status, 'response': char, 'session_id': session_id, 'finish': False}}, ensure_ascii=False)}\n\n"
                    time.sleep(0.01)
            # 发送元数据（diagnosis_result + finish）
            meta_data = {
                'code': 0,
                'data': {
                    'status': status,
                    'response': '',
                    'session_id': session_id,
                    'finish': finish,
                    'diagnosis_result': {
                        'syndrome': diagnosis.syndrome if diagnosis else '',
                        'prescription': diagnosis.prescription if diagnosis else '',
                        'ingredients': diagnosis.ingredients if diagnosis else [],
                        'department': diagnosis.department if diagnosis else '',
                        'allergy_warnings': diagnosis.allergy_warnings if diagnosis else [],
                        'therapy': diagnosis.therapy if diagnosis else '',
                        'precautions': diagnosis.precautions if diagnosis else '',
                    } if diagnosis else {},
                }
            }
            yield f"data: [METADATA]\n\n"
            yield f"data: {json.dumps(meta_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return

    session_data = {
        "last_access_time": time.time(),
        "is_diagnosed": existing_state.get("is_diagnosed", False),
    }
    _SESSIONS[store_key] = session_data

    finish = existing_state.get("is_diagnosed", False)
    full_response = json.dumps({
        'code': 0,
        'data': {
            'status': 'done',
            'response': '处理完成',
            'session_id': session_id,
            'finish': finish,
        }
    }, ensure_ascii=False)
    yield f"data: {full_response}\n\n"
    yield "data: [DONE]\n\n"


def tcm_agent_chat(session_id: str, patient_id: str, user_input: str, mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 开始对话 ======")
    logger.debug("agent_session_started scene=%s", scene)
    logger.debug("agent_input_received length=%s", len(user_input))
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] mode={mode}, scene={scene}")

    import json
    config = {"configurable": {"thread_id": session_id}}
    store_key = _session_key(session_id, patient_id, scene)

    allergy_herbs = []
    if patient_profile:
        allergy_info = patient_profile.get("allergy_history", {})
        if isinstance(allergy_info, dict):
            allergy_herbs = allergy_info.get("herbs", [])
        elif isinstance(allergy_info, list):
            allergy_herbs = allergy_info

    existing_state = _SESSIONS.get(store_key, {})

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 读取session状态 ======")
    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] existing_state keys: {list(existing_state.keys())}")
    if existing_state.get("symptoms_info"):
        si = existing_state["symptoms_info"]
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 已有symptoms_info: symptoms={si.symptoms}, tongue={si.tongue}, pulse={si.pulse}")

    if mode == "follow-up" and existing_state.get("symptoms_info"):
        preserved_symptoms = existing_state["symptoms_info"]
        preserved_diagnosis = existing_state.get("diagnosis_result")
        preserved_kg = existing_state.get("kg_raw_result")
    elif existing_state.get("symptoms_info"):
        preserved_symptoms = existing_state["symptoms_info"]
        preserved_diagnosis = existing_state.get("diagnosis_result")
        preserved_kg = existing_state.get("kg_raw_result")
    else:
        preserved_symptoms = None
        preserved_diagnosis = None
        preserved_kg = None

    preserved_messages = existing_state.get("messages", []) or []
    if not any(getattr(m, "content", None) == user_input for m in preserved_messages):
        preserved_messages = preserved_messages + [HumanMessage(content=user_input)]
    
    MAX_MESSAGES = 20
    if len(preserved_messages) > MAX_MESSAGES:
        preserved_messages = preserved_messages[-MAX_MESSAGES:]
    
    inputs = {
        "session_id": session_id,
        "patient_id": patient_id,
        "user_input": user_input,
        "mode": mode,
        "scene": scene,
        "messages": preserved_messages,
        "intent": None,
        "ask_question": None,
        "symptoms_info": preserved_symptoms,
        "kg_raw_result": preserved_kg,
        "diagnosis_result": preserved_diagnosis,
        "patient_profile": patient_profile if patient_profile else existing_state.get("patient_profile"),
        "allergy_herbs": allergy_herbs if allergy_herbs else existing_state.get("allergy_herbs", []),
        "final_response": None,
        "ask_round": existing_state.get("ask_round", 0),
        "refuse_count": existing_state.get("refuse_count", 0),
        "force_diagnosis": existing_state.get("force_diagnosis", False),
        "department_hint": existing_state.get("department_hint"),
    }

    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 调用 Agent ======")

    try:
        result = app.invoke(inputs, config)
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== Agent 调用完成 ======")
        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] intent={result.get('intent')}, has_diagnosis={result.get('diagnosis_result') is not None}")
    except Exception as e:
        logger.exception("agent_chat_failed")
        return {
            "status": "error",
            "response": "智能助手暂不可用，请稍后再试",
        }

    if result.get("intent") == "ask":
        si = result.get("symptoms_info")
        default_ask = "请提供患者症状信息，我来协助您辨证分析。" if scene == "doctor" else "请描述您的症状，我来帮您分析。"
        ask_q = result.get("ask_question") or default_ask

        session_data = dict(result)
        session_data["last_access_time"] = time.time()

        is_diagnosed = result.get("is_diagnosed", False) or existing_state.get("is_diagnosed", False)
        session_data["is_diagnosed"] = is_diagnosed

        # 诊断完成后，如果患者提出新问题（非追问症状），用LLM正常回答
        if is_diagnosed:
            # 检查是否是真正的症状追问，还是患者在问其他问题
            # 如果ask_question包含"舌象""脉象""症状"等追问关键词，说明是正常追问
            # 否则说明患者问的是其他问题（如"舌象和脉象怎么测"），需要用LLM正常回答
            _ask_followup_keywords = ["请提供", "请补充", "还需要", "请描述", "为了", "缺少", "缺失"]
            _is_real_followup = any(kw in ask_q for kw in _ask_followup_keywords) and ask_q != default_ask
            if not _is_real_followup:
                # 患者问的不是症状追问，用LLM正常回答
                try:
                    llm = _get_llm_32b()
                    from langchain_core.messages import SystemMessage
                    if scene == "guide":
                        sys_prompt = "你是一位温和、专业的中医健康助手。患者已完成预问诊诊断，现在提出了一个问题，请基于已有上下文友好回答。如果患者问的是如何测量舌象脉象等知识性问题，请详细指导。回答简洁明了。"
                    else:
                        sys_prompt = "你是一位专业的中医师助理。请基于已有上下文回答医生的问题。"
                    recent_msgs = existing_state.get("messages", [])[-6:]
                    context_str = "\n".join([f"{m.type}: {m.content}" for m in recent_msgs]) if recent_msgs else ""
                    human_content = f"患者问题：{user_input}\n\n对话历史：\n{context_str}" if context_str else user_input
                    response = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=human_content)])
                    ask_q = response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 诊断后回答失败: {e}")

            _SESSIONS[store_key] = session_data
            return {
                "status": "done",
                "response": ask_q,
                "finish": True,
            }
        _SESSIONS[store_key] = session_data

        logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ====== 保存session状态 ======")
        si = session_data.get("symptoms_info")
        if si and isinstance(si, SymptomsInfo):
            logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 保存symptoms_info: symptoms={si.symptoms}, tongue={si.tongue}, pulse={si.pulse}")
        else:
            logger.debug(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] symptoms_info为空或类型错误: {type(si)}")

        return {
            "status": "asking",
            "response": ask_q,
            "symptoms_info": si.dict() if isinstance(si, SymptomsInfo) else {},
            "finish": False,
        }

    if result.get("final_response"):
        intent = result.get("intent", "")
        diagnosis = result.get("diagnosis_result")
        session_data = dict(result)
        session_data["last_access_time"] = time.time()

        is_diagnosed = result.get("is_diagnosed", False) or existing_state.get("is_diagnosed", False)
        session_data["is_diagnosed"] = is_diagnosed

        _SESSIONS[store_key] = session_data

        if intent in ("custom_query", "medical_case"):
            return {
                "status": "query_answer",
                "response": result["final_response"],
                "finish": False,
            }
        if diagnosis:
            return {
                "status": "diagnosed",
                "response": result["final_response"],
                "diagnosis_result": {
                    "syndrome": diagnosis.syndrome if diagnosis else "",
                    "prescription": diagnosis.prescription if diagnosis else "",
                    "ingredients": diagnosis.ingredients if diagnosis else [],
                    "department": diagnosis.department if diagnosis else "",
                    "allergy_warnings": diagnosis.allergy_warnings if diagnosis else [],
                    "therapy": diagnosis.therapy if diagnosis else "",
                    "precautions": diagnosis.precautions if diagnosis else "",
                } if diagnosis else {},
                "finish": True,
            }

        if session_data.get("is_diagnosed"):
            return {
                "status": "done",
                "response": result["final_response"],
                "finish": True,
            }

        return {
            "status": "done",
            "response": result["final_response"],
            "finish": False,
        }

    session_data = {
        "last_access_time": time.time(),
        "is_diagnosed": existing_state.get("is_diagnosed", False),
    }
    _SESSIONS[store_key] = session_data

    if existing_state.get("is_diagnosed"):
        return {
            "status": "done",
            "response": "处理完成",
            "finish": True,
        }

    return {
        "status": "done",
        "response": "处理完成",
        "finish": False,
    }


if __name__ == "__main__":
    patient_profile = {
        "allergy_history": {"herbs": ["麻黄", "桂枝"]},
    }

    result = tcm_agent_chat(
        session_id="test_001",
        patient_id="p001",
        user_input="我最近头痛，发寒，无汗",
        mode="normal",
        scene="guide",
        patient_profile=patient_profile,
    )
    logger.debug(result)
