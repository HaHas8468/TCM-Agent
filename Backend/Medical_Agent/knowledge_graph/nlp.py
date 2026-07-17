import os
import re
from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


class EntityRecognizer:
    def __init__(self):
        self.llm = None
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            self.llm = ChatTongyi(
                model_name=os.getenv('LLM_MODEL_32B', 'qwen-max'),
                dashscope_api_key=api_key,
                temperature=0.1
            )
        
        self.symptom_patterns = [
            r'恶寒|发热|头痛|身痛|无汗|有汗|咽喉肿痛|鼻塞流涕|咳嗽|咳痰|气喘',
            r'神疲乏力|少气懒言|自汗|盗汗|心悸|失眠|头晕|眼花|耳鸣|健忘',
            r'口干|口苦|口臭|口渴|腹胀|腹痛|便秘|腹泻|食欲不振|恶心|呕吐',
            r'畏寒|肢冷|面色苍白|面色萎黄|面色潮红|小便清长|小便短黄|大便溏薄',
            r'胸闷|胸痛|疼痛拒按|烦躁|易怒|抑郁|焦虑|多梦|易醒',
            r'肢体麻木|关节疼痛|腰膝酸软|下肢水肿|皮肤瘙痒|皮疹',
            r'发热恶寒|寒热往来|午后潮热|夜间发热|手足心热',
            r'鼻塞|流涕|打喷嚏|咽痛|声音嘶哑|吞咽困难',
            r'腹胀满|腹痛拒按|嗳腐吞酸|不思饮食|食后腹胀',
            r'心悸心慌|胸闷气短|呼吸困难|喘息|胸闷如窒',
            r'头晕目眩|头痛如裂|头痛如裹|偏头痛|巅顶痛',
            r'肢体沉重|四肢不温|四肢厥冷|手足抽搐|肢体震颤',
            r'月经不调|痛经|闭经|带下异常|恶露不尽',
            r'口苦咽干|口淡无味|口中黏腻|牙龈肿痛|口舌生疮',
            r'大便干结|大便稀溏|大便脓血|里急后重|排便不爽'
        ]
        
        self.tongue_patterns = [
            r'舌红|舌淡|舌紫|舌暗|舌苔白|舌苔黄|舌苔厚|舌苔薄|舌苔腻|舌苔滑',
            r'舌体胖|舌体瘦|舌有齿痕|舌下脉络|舌尖红|舌边红|舌中裂纹',
            r'舌绛|舌淡白|舌淡胖|舌瘀斑|舌瘀点|舌痿软|舌强硬',
            r'舌苔灰黑|舌苔剥落|舌苔润燥|舌质苍老|舌质娇嫩'
        ]
        
        self.pulse_patterns = [
            r'脉浮|脉沉|脉数|脉迟|脉细|脉涩|脉弦|脉滑|脉紧|脉虚|脉实',
            r'脉洪|脉濡|脉缓|脉结|脉代|脉弱|脉微|脉促|脉长|脉短',
            r'脉大|脉小|脉芤|脉革|脉牢|脉动|脉疾|脉静|脉弦紧|脉滑数',
            r'脉沉细|脉沉迟|脉浮紧|脉浮数|脉细数|脉弦数|脉濡缓'
        ]

        self.zheng_keywords = {
            "风寒": ["恶寒", "无汗", "头痛", "身痛", "鼻塞流清涕", "舌苔薄白", "脉浮紧"],
            "风热": ["发热", "有汗", "咽喉肿痛", "口渴", "鼻塞流黄涕", "舌苔薄黄", "脉浮数"],
            "气虚": ["神疲乏力", "少气懒言", "自汗", "面色苍白", "脉虚"],
            "血虚": ["面色苍白", "头晕眼花", "心悸失眠", "手足发麻", "脉细"],
            "阴虚": ["口干咽燥", "潮热盗汗", "舌红少苔", "脉细数"],
            "阳虚": ["畏寒肢冷", "面色苍白", "小便清长", "大便溏薄", "脉沉迟"],
            "血瘀": ["疼痛拒按", "瘀斑瘀点", "舌紫暗", "脉涩"],
            "痰湿": ["咳嗽痰多", "胸闷腹胀", "舌苔白腻", "脉滑"],
            "气滞": ["胸闷", "腹胀", "嗳气", "易怒", "脉弦"],
            "食积": ["腹胀满", "嗳腐吞酸", "不思饮食", "舌苔厚腻"],
            "湿热": ["口苦", "口干", "大便溏而不爽", "小便短黄", "舌苔黄腻"],
            "寒湿": ["畏寒", "腹胀", "大便溏薄", "舌苔白腻", "脉濡缓"],
            "肝郁": ["胸闷", "易怒", "胁痛", "脉弦"],
            "脾虚": ["食欲不振", "腹胀", "大便溏薄", "神疲乏力", "面色萎黄"],
            "肾虚": ["腰膝酸软", "头晕耳鸣", "夜尿多", "早泄", "脉沉细"]
        }

    def extract_symptoms(self, text):
        symptoms = []
        for pattern in self.symptom_patterns:
            matches = re.findall(pattern, text)
            symptoms.extend(matches)
        return list(set(symptoms))

    def extract_tongue(self, text):
        tongue = []
        for pattern in self.tongue_patterns:
            matches = re.findall(pattern, text)
            tongue.extend(matches)
        return list(set(tongue))

    def extract_pulse(self, text):
        pulse = []
        for pattern in self.pulse_patterns:
            matches = re.findall(pattern, text)
            pulse.extend(matches)
        return list(set(pulse))

    def extract_entities_with_llm(self, text):
        if self.llm:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个中医药实体识别专家。请从以下文本中提取中医相关实体。"),
                ("human", "请分析以下文本，提取其中的中医症状、舌象、脉象等实体：\n\n{text}\n\n请以JSON格式返回，包含以下字段：\n- symptoms: 症状列表\n- tongue: 舌象列表\n- pulse: 脉象列表\n- zheng_types: 可能的证型列表（根据症状推测）")
            ])
            chain = prompt | self.llm
            response = chain.invoke({"text": text})
            try:
                import json
                return json.loads(response.content)
            except:
                return self._fallback_extraction(text)
        else:
            return self._fallback_extraction(text)

    def _fallback_extraction(self, text):
        symptoms = self.extract_symptoms(text)
        tongue = self.extract_tongue(text)
        pulse = self.extract_pulse(text)
        zheng_types = self._predict_zheng_from_keywords(symptoms, tongue, pulse)
        return {
            "symptoms": symptoms,
            "tongue": tongue,
            "pulse": pulse,
            "zheng_types": zheng_types
        }

    def _predict_zheng_from_keywords(self, symptoms, tongue, pulse):
        all_signs = symptoms + tongue + pulse
        zheng_scores = {}
        for zheng, keywords in self.zheng_keywords.items():
            score = sum(1 for kw in keywords if any(kw in sign for sign in all_signs))
            if score >= 2:
                zheng_scores[zheng] = score
        return sorted(zheng_scores.keys(), key=lambda x: zheng_scores[x], reverse=True)[:3]


class ZhengClassifier:
    def __init__(self):
        self.llm = None
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            self.llm = ChatTongyi(
                model_name=os.getenv('LLM_MODEL_32B', 'qwen-max'),
                dashscope_api_key=api_key,
                temperature=0.1
            )

    def classify_zheng(self, symptoms, tongue=None, pulse=None, other_signs=None):
        if self.llm:
            context = f"症状：{', '.join(symptoms)}"
            if tongue:
                context += f"\n舌象：{', '.join(tongue)}"
            if pulse:
                context += f"\n脉象：{', '.join(pulse)}"
            if other_signs:
                context += f"\n其他体征：{other_signs}"

            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个中医辨证专家。请根据患者的症状、舌象、脉象等信息进行辨证分型。"),
                ("human", "请根据以下患者信息进行中医辨证：\n\n{context}\n\n请以JSON格式返回，包含以下字段：\n- zheng_type: 最可能的证型名称\n- confidence: 置信度（0-1）\n- description: 证型描述\n- reasoning: 辨证依据")
            ])
            chain = prompt | self.llm
            response = chain.invoke({"context": context})
            try:
                import json
                return json.loads(response.content)
            except:
                return {
                    "zheng_type": "未确定",
                    "confidence": 0,
                    "description": "",
                    "reasoning": ""
                }
        else:
            return {
                "zheng_type": "未确定",
                "confidence": 0,
                "description": "",
                "reasoning": "LLM未配置"
            }

    def classify_zheng_with_knowledge_graph(self, symptoms, tongue=None, pulse=None, other_signs=None):
        from .queries import DiagnosisQueries
        kg_results = DiagnosisQueries.get_zheng_by_symptoms(symptoms)
        
        context = f"症状：{', '.join(symptoms)}"
        if tongue:
            context += f"\n舌象：{', '.join(tongue)}"
        if pulse:
            context += f"\n脉象：{', '.join(pulse)}"
        if other_signs:
            context += f"\n其他体征：{other_signs}"
        
        kg_context = "\n知识图谱匹配结果：\n"
        for result in kg_results[:5]:
            kg_context += f"- {result['zheng_type']}: 匹配{result['symptom_count']}个症状，匹配率{result.get('match_rate', 0)*100:.0f}%\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个中医辨证专家。请结合知识图谱匹配结果和患者信息进行辨证分型。"),
            ("human", "请根据以下患者信息和知识图谱匹配结果进行中医辨证：\n\n{context}\n\n{kg_context}\n\n请以JSON格式返回，包含以下字段：\n- zheng_type: 最可能的证型名称\n- confidence: 置信度（0-1）\n- description: 证型描述\n- reasoning: 辨证依据\n- knowledge_graph_reference: 参考的知识图谱匹配结果")
        ])
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "kg_context": kg_context})
        try:
            import json
            result = json.loads(response.content)
            result['knowledge_graph_reference'] = kg_results[:5]
            return result
        except:
            return {
                "zheng_type": kg_results[0]['zheng_type'] if kg_results else "未确定",
                "confidence": kg_results[0].get('match_rate', 0) if kg_results else 0,
                "description": kg_results[0].get('description', '') if kg_results else "",
                "reasoning": "基于知识图谱匹配结果",
                "knowledge_graph_reference": kg_results[:5]
            }


class DiagnosisAgent:
    def __init__(self):
        self.llm = None
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            self.llm = ChatTongyi(
                model_name=os.getenv('LLM_MODEL_32B', 'qwen-max'),
                dashscope_api_key=api_key,
                temperature=0.1
            )
        self.entity_recognizer = EntityRecognizer()
        self.zheng_classifier = ZhengClassifier()
        self.diagnosis_history = []

    def start_diagnosis(self):
        self.diagnosis_history = []
        return {
            "message": "请描述您的症状，例如：我最近感觉头痛、发热、鼻塞流涕",
            "next_step": "collect_symptoms"
        }

    def collect_and_analyze(self, user_input):
        entities = self.entity_recognizer.extract_entities_with_llm(user_input)
        self.diagnosis_history.append({
            "user_input": user_input,
            "entities": entities
        })
        
        symptoms = entities.get('symptoms', [])
        tongue = entities.get('tongue', [])
        pulse = entities.get('pulse', [])
        
        if not symptoms and not tongue and not pulse:
            return {
                "message": "我没有识别到明确的症状，请更详细地描述您的不适，例如：头痛、发热、咳嗽等",
                "next_step": "collect_symptoms",
                "entities": entities
            }
        
        if len(symptoms) < 3:
            return {
                "message": f"已识别到症状：{', '.join(symptoms)}。为了更准确地辨证，请补充描述舌象（如舌苔颜色）、脉象（如脉浮、脉细）或其他不适症状",
                "next_step": "collect_more_info",
                "entities": entities
            }
        
        classification = self.zheng_classifier.classify_zheng_with_knowledge_graph(
            symptoms, tongue, pulse
        )
        
        return {
            "message": f"根据您的症状，初步辨证为【{classification['zheng_type']}】，置信度：{classification['confidence']*100:.0f}%",
            "next_step": "confirm_diagnosis",
            "entities": entities,
            "classification": classification
        }

    def get_recommendation(self, zheng_type):
        from .queries import FormulaQueries
        formulas = FormulaQueries.get_formulas_by_zheng(zheng_type)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个中医方剂推荐专家。请根据证型推荐合适的方剂。"),
            ("human", "证型：{zheng_type}\n\n候选方剂：\n{formulas}\n\n请以JSON格式返回推荐结果，包含以下字段：\n- recommended_formula: 推荐方剂名称\n- alternatives: 备选方剂列表\n- rationale: 推荐理由")
        ])
        
        formulas_text = "\n".join([f"- {f['formula_name']}: {f['effect']}" for f in formulas[:5]])
        chain = prompt | self.llm
        response = chain.invoke({"zheng_type": zheng_type, "formulas": formulas_text})
        
        try:
            import json
            result = json.loads(response.content)
            result['candidate_formulas'] = formulas[:5]
            return result
        except:
            return {
                "recommended_formula": formulas[0]['formula_name'] if formulas else "无推荐方剂",
                "alternatives": [f['formula_name'] for f in formulas[1:4]] if len(formulas) > 1 else [],
                "rationale": "基于证型匹配推荐",
                "candidate_formulas": formulas[:5]
            }


entity_recognizer = EntityRecognizer()
zheng_classifier = ZhengClassifier()
diagnosis_agent = DiagnosisAgent()
