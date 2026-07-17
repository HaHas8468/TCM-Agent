export const doctorPrototypeSeed = {
  navigationItems: [
    {
      key: 'queue',
      label: '接诊队列',
      description: '查看今日挂号患者，按科室与初复诊快速分流。'
    },
    {
      key: 'records',
      label: '病历管理',
      description: '按姓名、patient_id、证型与就诊时间检索历史门诊病历。'
    },
    {
      key: 'cases',
      label: '个人医案库',
      description: '检索、录入并维护医生个人临床医案。'
    },
    {
      key: 'settings',
      label: '用户设置',
      description: ''
    }
  ],
  doctorProfile: {
    name: '林知夏',
    title: '中医内科主任医师',
    role: '管理员',
    account: 'doctor.lin',
    department: '中医内科',
    organization: '青囊中医院智慧门诊',
    shift: '全天 9:00-5:30',
    focus: '脾胃病、肺系病、亚健康调理',
    dutyStatus: '值班'
  },
  patients: [],
  records: [],
  settings: {
    profile: {
      name: '林知夏',
      title: '中医内科主任医师',
      role: '管理员',
      account: 'doctor.lin',
      phone: '138****8612',
      email: 'lin.zhixia@qingnang-hospital.cn',
      department: '中医内科',
      clinicRoom: '门诊楼 3F 07 诊室',
      organization: '青囊中医院智慧门诊',
      shift: '全天 9:00-5:30',
      focus: '脾胃病、肺系病、亚健康调理',
      bio: '负责医生端 AI 辅助诊疗流程验证，关注门诊效率与病历归档质量。',
      signature: '辨证求因，处方求稳。'
    },
    notifications: {
      queueReminder: true,
      followUpReminder: true,
      urgentAlert: true,
      aiCompletionNotice: false,
      emailDigest: true,
      smsFallback: false,
      digestTime: '18:00'
    },
    workspace: {
      defaultLandingModule: 'queue',
      queueAutoRefresh: true,
      autoRefreshSeconds: 45,
      showAiEvidence: true,
      compactSidebar: false,
      openKnowledgeDrawer: true,
      autoArchiveFinished: false
    },
    security: {
      twoFactorEnabled: true,
      loginProtection: true,
      deviceReviewRequired: false,
      sessionTimeoutMinutes: 30,
      lastPasswordUpdate: '2026-06-21',
      lastLogin: '2026-07-06 11:12',
      trustedDevices: 3
    },
    integrations: [
      {
        name: 'LangGraph 智能助手',
        status: '运行正常',
        detail: '医生辅助诊疗响应中位耗时 1.8 秒，scene=doctor 通道稳定。',
        owner: 'AI 平台组'
      },
      {
        name: 'Neo4j 知识图谱',
        status: '需关注',
        detail: '妇科经典医案映射待补齐，推荐详情命中率需继续观察。',
        owner: '知识工程组'
      },
      {
        name: '门诊消息网关',
        status: '运行正常',
        detail: '挂号提醒、复诊提醒与高优先级预警均可正常下发。',
        owner: '中台运维'
      },
      {
        name: '登录安全服务',
        status: '待处理',
        detail: '普通医师二次验证策略待统一下发，当前仅管理员启用。',
        owner: '安全平台主管'
      }
    ],
    activity: [
      {
        time: '2026-07-06 11:32',
        action: '更新门诊提醒策略并开启队列提醒',
        operator: '林知夏'
      },
      {
        time: '2026-07-06 10:54',
        action: '调整默认进入模块为接诊队列',
        operator: '林知夏'
      },
      {
        time: '2026-07-06 09:18',
        action: '完成管理员账号安全检查',
        operator: '系统管理员'
      }
    ]
  }
}

