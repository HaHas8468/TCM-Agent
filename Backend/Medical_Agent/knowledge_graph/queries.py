from .neo4j_connection import neo4j_conn


class DiagnosisQueries:
    @staticmethod
    def get_zheng_by_symptoms(symptoms):
        cypher = """
            MATCH (s:症状)-[:属于]->(z:证型)
            WHERE s.name IN $symptoms
            RETURN z.name AS zheng_type, z.description AS description,
                   COUNT(s) AS symptom_count,
                   ROUND(COUNT(s) * 1.0 / $total_symptoms, 2) AS match_rate
            ORDER BY symptom_count DESC
            LIMIT 10
        """
        return neo4j_conn.query(cypher, {"symptoms": symptoms, "total_symptoms": len(symptoms)})

    @staticmethod
    def get_zheng_details(zheng_type):
        cypher = """
            MATCH (z:证型 {name: $zheng_type})
            OPTIONAL MATCH (z)-[:典型症状]->(s:症状)
            OPTIONAL MATCH (z)-[:典型舌象]->(t:舌象)
            OPTIONAL MATCH (z)-[:典型脉象]->(p:脉象)
            OPTIONAL MATCH (z)-[:治法]->(m:治法)
            OPTIONAL MATCH (f:方剂)-[:主治]->(z)
            RETURN z.name AS zheng_type, z.description AS description,
                   COLLECT(DISTINCT s.name) AS symptoms,
                   COLLECT(DISTINCT t.name) AS tongue_signs,
                   COLLECT(DISTINCT p.name) AS pulse_signs,
                   COLLECT(DISTINCT m.name) AS treatments,
                   COLLECT(DISTINCT f.name) AS related_formulas
        """
        result = neo4j_conn.query(cypher, {"zheng_type": zheng_type})
        return result[0] if result else None

    @staticmethod
    def get_all_zheng_types():
        cypher = """
            MATCH (z:证型)
            RETURN z.name AS zheng_type, z.description AS description
            ORDER BY z.name
        """
        return neo4j_conn.query(cypher)

    @staticmethod
    def get_zheng_relations(zheng_type):
        cypher = """
            MATCH (z:证型 {name: $zheng_type})
            OPTIONAL MATCH (z)-[:兼夹]->(z2:证型)
            OPTIONAL MATCH (z2)-[:兼夹]->(z)
            OPTIONAL MATCH (z)-[:转化]->(z3:证型)
            RETURN z.name AS zheng_type,
                   COLLECT(DISTINCT z2.name) AS combined_with,
                   COLLECT(DISTINCT z3.name) AS can_transform_to
        """
        result = neo4j_conn.query(cypher, {"zheng_type": zheng_type})
        return result[0] if result else None

    @staticmethod
    def get_symptom_zheng_path(symptom_name):
        cypher = """
            MATCH path = (s:症状 {name: $symptom_name})-[:属于*1..3]->(z:证型)
            RETURN [n in nodes(path) | n.name] AS path,
                   [r in relationships(path) | type(r)] AS relations
            LIMIT 10
        """
        return neo4j_conn.query(cypher, {"symptom_name": symptom_name})


class FormulaQueries:
    @staticmethod
    def get_formulas_by_zheng(zheng_type):
        cypher = """
            MATCH (f:方剂)-[:主治]->(z:证型 {name: $zheng_type})
            OPTIONAL MATCH (f)-[:组成]->(h:中药)
            RETURN f.name AS formula_name, f.description AS description,
                   f.effect AS effect, f.source AS source,
                   f.decoction_method AS decoction_method,
                   COLLECT(DISTINCT h.name) AS herbs,
                   SIZE(COLLECT(DISTINCT h.name)) AS herb_count
            ORDER BY f.name
        """
        return neo4j_conn.query(cypher, {"zheng_type": zheng_type})

    @staticmethod
    def get_formula_details(formula_name):
        cypher = """
            MATCH (f:方剂 {name: $formula_name})
            OPTIONAL MATCH (f)-[:组成]->(h:中药)
            OPTIONAL MATCH (f)-[:主治]->(z:证型)
            OPTIONAL MATCH (f)-[:加减]->(m:加减建议)
            OPTIONAL MATCH (f)-[:药理研究]->(p:药理研究)
            OPTIONAL MATCH (f)-[:来源]->(s:文献)
            RETURN f.name AS formula_name, f.description AS description,
                   f.effect AS effect, f.source AS source,
                   f.decoction_method AS decoction_method,
                   f.usage AS usage,
                   COLLECT(DISTINCT h.name) AS herbs,
                   COLLECT(DISTINCT z.name) AS indications,
                   COLLECT(DISTINCT m.content) AS modifications,
                   COLLECT(DISTINCT p.content) AS pharmacology,
                   COLLECT(DISTINCT s.name) AS sources
        """
        result = neo4j_conn.query(cypher, {"formula_name": formula_name})
        return result[0] if result else None

    @staticmethod
    def search_formulas(keyword):
        cypher = """
            MATCH (f:方剂)
            WHERE f.name CONTAINS $keyword OR f.description CONTAINS $keyword
            OR f.effect CONTAINS $keyword
            RETURN f.name AS formula_name, f.description AS description, 
                   f.effect AS effect, f.source AS source
            LIMIT 20
        """
        return neo4j_conn.query(cypher, {"keyword": keyword})

    @staticmethod
    def get_formulas_by_herb(herb_name):
        cypher = """
            MATCH (f:方剂)-[:组成]->(h:中药 {name: $herb_name})
            RETURN f.name AS formula_name, f.description AS description,
                   f.effect AS effect, f.source AS source
            ORDER BY f.name
            LIMIT 20
        """
        return neo4j_conn.query(cypher, {"herb_name": herb_name})

    @staticmethod
    def get_formula_composition_ratio(formula_name):
        cypher = """
            MATCH (f:方剂 {name: $formula_name})-[:组成]->(h:中药)
            RETURN h.name AS herb_name, h.property AS property, h.flavor AS flavor,
                   h.effect AS effect
            ORDER BY h.name
        """
        return neo4j_conn.query(cypher, {"formula_name": formula_name})

    @staticmethod
    def get_all_formulas():
        cypher = """
            MATCH (f:方剂)
            RETURN f.name AS formula_name, f.description AS description,
                   f.effect AS effect, f.source AS source
            ORDER BY f.name
            LIMIT 50
        """
        return neo4j_conn.query(cypher)


class HerbQueries:
    @staticmethod
    def get_herb_details(herb_name):
        cypher = """
            MATCH (h:中药 {name: $herb_name})
            OPTIONAL MATCH (h)-[:归经]->(m:经络)
            OPTIONAL MATCH (h)-[:配伍]->(h2:中药)
            OPTIONAL MATCH (h)-[:禁忌]->(c:禁忌)
            OPTIONAL MATCH (h)-[:现代研究]->(r:现代研究)
            OPTIONAL MATCH (h)-[:毒性]->(t:毒性)
            OPTIONAL MATCH (f:方剂)-[:组成]->(h)
            RETURN h.name AS herb_name, h.property AS property,
                   h.flavor AS flavor, h.effect AS effect,
                   h.dosage AS dosage, h.description AS description,
                   h.pinyin AS pinyin,
                   COLLECT(DISTINCT m.name) AS meridians,
                   COLLECT(DISTINCT h2.name) AS compatibility,
                   COLLECT(DISTINCT c.content) AS contraindications,
                   COLLECT(DISTINCT r.content) AS modern_research,
                   COLLECT(DISTINCT t.content) AS toxicity,
                   COLLECT(DISTINCT f.name) AS used_in_formulas
        """
        result = neo4j_conn.query(cypher, {"herb_name": herb_name})
        return result[0] if result else None

    @staticmethod
    def search_herbs(keyword):
        cypher = """
            MATCH (h:中药)
            WHERE h.name CONTAINS $keyword OR h.description CONTAINS $keyword
            OR h.effect CONTAINS $keyword OR h.pinyin CONTAINS $keyword
            RETURN h.name AS herb_name, h.property AS property,
                   h.flavor AS flavor, h.effect AS effect,
                   h.pinyin AS pinyin
            LIMIT 20
        """
        return neo4j_conn.query(cypher, {"keyword": keyword})

    @staticmethod
    def get_herbs_by_property(property_name):
        cypher = """
            MATCH (h:中药 {property: $property_name})
            RETURN h.name AS herb_name, h.flavor AS flavor, h.effect AS effect,
                   h.pinyin AS pinyin
            ORDER BY h.name
        """
        return neo4j_conn.query(cypher, {"property_name": property_name})

    @staticmethod
    def get_herbs_by_meridian(meridian_name):
        cypher = """
            MATCH (h:中药)-[:归经]->(m:经络 {name: $meridian_name})
            RETURN h.name AS herb_name, h.property AS property, h.flavor AS flavor,
                   h.effect AS effect
            ORDER BY h.name
        """
        return neo4j_conn.query(cypher, {"meridian_name": meridian_name})

    @staticmethod
    def get_herbs_by_flavor(flavor):
        cypher = """
            MATCH (h:中药)
            WHERE h.flavor CONTAINS $flavor
            RETURN h.name AS herb_name, h.property AS property, h.effect AS effect
            ORDER BY h.name
            LIMIT 20
        """
        return neo4j_conn.query(cypher, {"flavor": flavor})

    @staticmethod
    def get_compatibility_relations(herb_name):
        cypher = """
            MATCH (h:中药 {name: $herb_name})
            OPTIONAL MATCH (h)-[r:配伍]->(h2:中药)
            OPTIONAL MATCH (h3:中药)-[r2:配伍]->(h)
            RETURN h.name AS herb_name,
                   COLLECT(DISTINCT {herb: h2.name, relation: type(r)}) AS compatible_with,
                   COLLECT(DISTINCT {herb: h3.name, relation: type(r2)}) AS compatible_by
        """
        result = neo4j_conn.query(cypher, {"herb_name": herb_name})
        return result[0] if result else None

    @staticmethod
    def get_all_herbs():
        cypher = """
            MATCH (h:中药)
            RETURN h.name AS herb_name, h.property AS property, h.flavor AS flavor,
                   h.effect AS effect, h.pinyin AS pinyin
            ORDER BY h.name
            LIMIT 100
        """
        return neo4j_conn.query(cypher)

    @staticmethod
    def get_all_properties():
        cypher = """
            MATCH (h:中药)
            RETURN DISTINCT h.property AS property
            ORDER BY property
        """
        return neo4j_conn.query(cypher)

    @staticmethod
    def get_all_meridians():
        cypher = """
            MATCH (m:经络)
            RETURN m.name AS meridian_name
            ORDER BY meridian_name
        """
        return neo4j_conn.query(cypher)


class MedicalRecordQueries:
    @staticmethod
    def search_records(disease_name=None, zheng_type=None, formula_name=None):
        conditions = []
        params = {}
        
        if disease_name:
            conditions.append("r.disease_name CONTAINS $disease_name")
            params["disease_name"] = disease_name
        if zheng_type:
            conditions.append("r.zheng_type CONTAINS $zheng_type")
            params["zheng_type"] = zheng_type
        if formula_name:
            conditions.append("r.formula_name CONTAINS $formula_name")
            params["formula_name"] = formula_name
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cypher = f"""
            MATCH (r:医案)
            WHERE {where_clause}
            RETURN r.title AS title, r.disease_name AS disease_name,
                   r.zheng_type AS zheng_type, r.formula_name AS formula_name,
                   r.content AS content, r.author AS author, r.source AS source
            ORDER BY r.title
            LIMIT 20
        """
        return neo4j_conn.query(cypher, params)

    @staticmethod
    def get_record_details(record_title):
        cypher = """
            MATCH (r:医案 {title: $record_title})
            OPTIONAL MATCH (r)-[:涉及]->(h:中药)
            OPTIONAL MATCH (r)-[:涉及方剂]->(f:方剂)
            OPTIONAL MATCH (r)-[:关联证型]->(z:证型)
            RETURN r.title AS title, r.disease_name AS disease_name,
                   r.zheng_type AS zheng_type, r.formula_name AS formula_name,
                   r.content AS content, r.author AS author, r.source AS source,
                   r.treatment_outcome AS treatment_outcome,
                   r.duration AS duration,
                   COLLECT(DISTINCT h.name) AS herbs,
                   COLLECT(DISTINCT f.name) AS formulas,
                   COLLECT(DISTINCT z.name) AS related_zheng_types
        """
        result = neo4j_conn.query(cypher, {"record_title": record_title})
        return result[0] if result else None

    @staticmethod
    def search_records_by_herb(herb_name):
        cypher = """
            MATCH (r:医案)-[:涉及]->(h:中药 {name: $herb_name})
            RETURN r.title AS title, r.disease_name AS disease_name,
                   r.zheng_type AS zheng_type, r.formula_name AS formula_name,
                   r.content AS content, r.author AS author
            ORDER BY r.title
            LIMIT 20
        """
        return neo4j_conn.query(cypher, {"herb_name": herb_name})

    @staticmethod
    def get_records_by_author(author_name):
        cypher = """
            MATCH (r:医案)
            WHERE r.author CONTAINS $author_name
            RETURN r.title AS title, r.disease_name AS disease_name,
                   r.zheng_type AS zheng_type, r.formula_name AS formula_name,
                   r.source AS source
            ORDER BY r.title
            LIMIT 20
        """
        return neo4j_conn.query(cypher, {"author_name": author_name})

    @staticmethod
    def get_all_records():
        cypher = """
            MATCH (r:医案)
            RETURN r.title AS title, r.disease_name AS disease_name,
                   r.zheng_type AS zheng_type, r.formula_name AS formula_name,
                   r.author AS author, r.source AS source
            ORDER BY r.title
            LIMIT 50
        """
        return neo4j_conn.query(cypher)

    @staticmethod
    def get_record_similarity(record_title):
        cypher = """
            MATCH (r:医案 {title: $record_title})-[:涉及]->(h:中药)
            MATCH (r2:医案)-[:涉及]->(h)
            WHERE r2.title <> $record_title
            RETURN r2.title AS similar_record,
                   COUNT(DISTINCT h) AS shared_herbs_count,
                   r2.disease_name AS disease_name,
                   r2.zheng_type AS zheng_type
            ORDER BY shared_herbs_count DESC
            LIMIT 10
        """
        return neo4j_conn.query(cypher, {"record_title": record_title})

    @staticmethod
    def get_all_diseases():
        cypher = """
            MATCH (r:医案)
            RETURN DISTINCT r.disease_name AS disease_name
            ORDER BY disease_name
        """
        return neo4j_conn.query(cypher)
