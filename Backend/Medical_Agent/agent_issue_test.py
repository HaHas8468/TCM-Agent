"""
针对新问题的测试脚本：
1. 饮食建议少字问题（"吃生冷油腻"应为"不吃/避免吃生冷油腻"）
2. 话题切换问题（问诊后询问人参功效，应返回药材信息而不是继续诊断）
"""
import os
import sys
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "traditional_medical_agent"))

from traditional_medical_agent.tcm_agent import tcm_agent_chat

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent问题修复测试结果.txt")


def write_log(text, append=True):
    print(text)
    mode = "a" if append else "w"
    with open(OUTPUT_FILE, mode, encoding="utf-8") as f:
        f.write(text + "\n")


def run_conversation(scene, session_id, inputs, profile=None):
    write_log("\n" + "="*80)
    write_log(f"【{'患者端' if scene == 'guide' else '医生端'}测试】会话={session_id}")
    write_log("="*80)
    for i, user_input in enumerate(inputs):
        mode = "normal" if i == 0 else "follow-up"
        label = "用户" if scene == "guide" else "医生"
        try:
            result = tcm_agent_chat(
                session_id=session_id,
                patient_id=f"p_{session_id}",
                user_input=user_input,
                mode=mode,
                scene=scene,
                patient_profile=profile
            )
            write_log(f"\n{label}：{user_input}")
            write_log(f"Agent状态：{result.get('status', 'unknown')}")
            write_log(f"Agent回复：{result.get('response', '无回复')}")
            if result.get('diagnosis_result'):
                write_log(f"诊断结果：{result.get('diagnosis_result')}")
        except Exception as e:
            write_log(f"\n{label}：{user_input}")
            write_log(f"错误：{str(e)}")
            write_log(traceback.format_exc())


def main():
    write_log("="*80, append=False)
    write_log("Agent问题修复测试 - 饮食建议少字 & 话题切换")
    write_log(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    write_log("="*80)

    # 测试1：饮食建议少字问题（复用用户截图中的对话）
    run_conversation(
        "guide", "diet_issue",
        [
            "我头晕腹痛挂什么课",
            "流鼻涕冒冷汗。不懂舌象脉象",
            "不方便提供",
        ]
    )

    # 测试2：话题切换问题（问诊后问人参功效）
    run_conversation(
        "guide", "topic_switch",
        [
            "我头晕腹痛挂什么课",
            "流鼻涕冒冷汗。不懂舌象脉象",
            "不方便提供",
            "人参有什么功效",
        ]
    )

    # 测试3：医生端话题切换
    run_conversation(
        "doctor", "topic_switch_doctor",
        [
            "患者头痛、失眠",
            "患者舌象发红",
            "脉象平滑",
            "麻黄有什么功效",
        ]
    )

    write_log("\n" + "="*80)
    write_log("测试完成")
    write_log("="*80)


if __name__ == "__main__":
    main()
