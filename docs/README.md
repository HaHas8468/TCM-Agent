# 项目文档

本目录是 TCM_Agent monorepo 的唯一项目文档入口。代码目录仅保留指向本目录的 README，避免前后端各自维护重复副本。

## 目录

- [api/](api/)：唯一 API 规范、患者端和医生端联调资料。
- [requirements/](requirements/)：完整功能需求、前端 PRD、Agent 内核需求与线上线下业务方案。
- [testing/](testing/)：系统、接口和 Agent 回归测试用例与报告。
- [design/](design/)：患者端视觉规范、医生端原型和界面说明。
- [guides/](guides/)：后端、Agent 内核、Neo4j 图谱与参考工具说明。

## 维护约定

- API 以 [API接口规范.md](api/API接口规范.md) 为唯一规范，修改后同步更新差异清单。
- 需求、设计、测试文档应按主题放入本目录，不再在 `Backend/` 或 `frontend/` 根目录新增副本。
- 与代码强绑定的说明文件仅保留简短入口，正文放在本目录。
