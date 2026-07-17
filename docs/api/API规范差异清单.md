# API 规范差异清单

## 唯一规范

[API接口规范.md](API接口规范.md) 是当前唯一规范，版本为 **v2.3**，来源于后端版本并采用 Markdown 结构化格式。

## 已合并的重复来源

患者端和医生端原有的 API 规范副本已移除。两份副本中的差异不直接提升为正式接口，保留如下，待后端实现后再纳入主规范：

| 来源 | 差异接口或内容 | 处理 |
| --- | --- | --- |
| 患者端 v2.3 副本 | `GET /api/orders/{order_id}/patient`、`GET /api/patients/bypatientid/{patient_id}/basic` | 待确认，未写入正式规范。 |
| 医生端 v2.2 副本 | `GET /api/patient/notifications`、`GET /api/patients/bypatientid/{patient_id}/basic` | v2.2 历史内容，待确认，未写入正式规范。 |
| 两个副本 | 文本格式、标题层级和示例排版不同 | 已去重，不再单独维护。 |

患者端与医生端的实际对接进度见本目录的 `patient-*.md` 和 `doctor-*.md` 文档。
