from .neo4j_connection import neo4j_conn


class KnowledgeGraphInitializer:
    @staticmethod
    def create_schema():
        schema_queries = [
            """CREATE CONSTRAINT IF NOT EXISTS FOR (s:症状) REQUIRE s.name IS UNIQUE""",
            """CREATE CONSTRAINT IF NOT EXISTS FOR (z:证型) REQUIRE z.name IS UNIQUE""",
            """CREATE CONSTRAINT IF NOT EXISTS FOR (f:方剂) REQUIRE f.name IS UNIQUE""",
            """CREATE CONSTRAINT IF NOT EXISTS FOR (h:中药) REQUIRE h.name IS UNIQUE""",
            """CREATE CONSTRAINT IF NOT EXISTS FOR (m:经络) REQUIRE m.name IS UNIQUE""",
            """CREATE CONSTRAINT IF NOT EXISTS FOR (r:医案) REQUIRE r.title IS UNIQUE""",
            """CREATE CONSTRAINT IF NOT EXISTS FOR (t:治法) REQUIRE t.name IS UNIQUE""",
            """CREATE CONSTRAINT IF NOT EXISTS FOR (c:禁忌) REQUIRE c.content IS UNIQUE""",
        ]
        for query in schema_queries:
            neo4j_conn.query(query)

    @staticmethod
    def init_basic_data():
        KnowledgeGraphInitializer._init_meridians()
        KnowledgeGraphInitializer._init_treatments()
        KnowledgeGraphInitializer._init_zheng_types()
        KnowledgeGraphInitializer._init_zheng_relations()
        KnowledgeGraphInitializer._init_symptoms()
        KnowledgeGraphInitializer._init_tongue_signs()
        KnowledgeGraphInitializer._init_pulse_signs()
        KnowledgeGraphInitializer._init_herbs()
        KnowledgeGraphInitializer._init_herb_compatibility()
        KnowledgeGraphInitializer._init_herb_contraindications()
        KnowledgeGraphInitializer._init_formulas()
        KnowledgeGraphInitializer._init_formula_modifications()
        KnowledgeGraphInitializer._init_medical_records()

    @staticmethod
    def _init_meridians():
        meridians = ['手太阴肺经', '手阳明大肠经', '足阳明胃经', '足太阴脾经',
                     '手少阴心经', '手太阳小肠经', '足太阳膀胱经', '足少阴肾经',
                     '手厥阴心包经', '手少阳三焦经', '足少阳胆经', '足厥阴肝经']
        for meridian in meridians:
            cypher = """MERGE (m:经络 {name: $name})"""
            neo4j_conn.query(cypher, {"name": meridian})

    @staticmethod
    def _init_treatments():
        treatments = [
            {"name": "辛温解表", "description": "用辛温发散药物治疗风寒感冒"},
            {"name": "辛凉解表", "description": "用辛凉发散药物治疗风热感冒"},
            {"name": "益气", "description": "用补气药物治疗气虚证"},
            {"name": "补血", "description": "用补血药物治疗血虚证"},
            {"name": "滋阴", "description": "用滋阴药物治疗阴虚证"},
            {"name": "温阳", "description": "用温阳药物治疗阳虚证"},
            {"name": "活血化瘀", "description": "用活血祛瘀药物治疗血瘀证"},
            {"name": "燥湿化痰", "description": "用燥湿化痰药物治疗痰湿证"},
            {"name": "疏肝理气", "description": "用疏肝理气药物治疗肝郁气滞证"},
            {"name": "健脾祛湿", "description": "用健脾祛湿药物治疗脾虚湿盛证"},
        ]
        for treatment in treatments:
            cypher = """MERGE (t:治法 {name: $name, description: $description})"""
            neo4j_conn.query(cypher, treatment)

    @staticmethod
    def _init_zheng_types():
        zheng_types = [
            {"name": "风寒感冒", "description": "外感风寒，卫阳被遏，表现为恶寒重、发热轻、无汗、头痛身痛等"},
            {"name": "风热感冒", "description": "外感风热，邪犯肺卫，表现为发热重、微恶风、有汗、咽喉肿痛等"},
            {"name": "气虚", "description": "元气不足，脏腑功能减退，表现为神疲乏力、少气懒言、自汗等"},
            {"name": "血虚", "description": "血液不足，脏腑失养，表现为面色苍白、头晕眼花、心悸失眠等"},
            {"name": "阴虚", "description": "阴液不足，虚热内生，表现为口干咽燥、潮热盗汗、舌红少苔等"},
            {"name": "阳虚", "description": "阳气不足，虚寒内生，表现为畏寒肢冷、面色苍白、小便清长等"},
            {"name": "血瘀", "description": "血液运行不畅，瘀滞体内，表现为疼痛拒按、瘀斑瘀点、舌紫暗等"},
            {"name": "痰湿", "description": "水湿内停，聚而成痰，表现为咳嗽痰多、胸闷腹胀、舌苔白腻等"},
            {"name": "气滞", "description": "气机郁滞不畅，表现为胸闷、腹胀、嗳气、易怒、脉弦等"},
            {"name": "肝郁气滞", "description": "肝气郁结，气机不畅，表现为胸闷胁痛、易怒、善太息等"},
            {"name": "脾虚", "description": "脾胃虚弱，运化失常，表现为食欲不振、腹胀、大便溏薄等"},
            {"name": "肾虚", "description": "肾脏功能减退，表现为腰膝酸软、头晕耳鸣、夜尿多等"},
            {"name": "湿热", "description": "湿邪与热邪交织，表现为口苦、口干、大便溏而不爽、舌苔黄腻等"},
            {"name": "寒湿", "description": "湿邪与寒邪交织，表现为畏寒、腹胀、大便溏薄、舌苔白腻等"},
            {"name": "食积", "description": "饮食停滞胃肠，表现为腹胀满、嗳腐吞酸、不思饮食等"},
        ]
        for zheng in zheng_types:
            cypher = """MERGE (z:证型 {name: $name, description: $description})"""
            neo4j_conn.query(cypher, zheng)

    @staticmethod
    def _init_zheng_relations():
        zheng_relations = [
            {"source": "气虚", "target": "阳虚", "relation": "转化"},
            {"source": "血虚", "target": "阴虚", "relation": "转化"},
            {"source": "血瘀", "target": "气滞", "relation": "兼夹"},
            {"source": "气滞", "target": "血瘀", "relation": "兼夹"},
            {"source": "痰湿", "target": "脾虚", "relation": "兼夹"},
            {"source": "脾虚", "target": "痰湿", "relation": "转化"},
            {"source": "肝郁气滞", "target": "脾虚", "relation": "兼夹"},
            {"source": "肾虚", "target": "脾虚", "relation": "兼夹"},
            {"source": "湿热", "target": "痰湿", "relation": "兼夹"},
            {"source": "风寒感冒", "target": "风热感冒", "relation": "转化"},
        ]
        for rel in zheng_relations:
            cypher = f"""
                MATCH (z1:证型 {{name: $source}}), (z2:证型 {{name: $target}})
                MERGE (z1)-[:{rel['relation']}]->(z2)
            """
            neo4j_conn.query(cypher, {"source": rel["source"], "target": rel["target"]})

    @staticmethod
    def _init_symptoms():
        symptoms = [
            {"name": "恶寒", "zheng": ["风寒感冒", "阳虚", "寒湿"]},
            {"name": "发热", "zheng": ["风寒感冒", "风热感冒", "湿热"]},
            {"name": "头痛", "zheng": ["风寒感冒", "风热感冒", "血瘀"]},
            {"name": "身痛", "zheng": ["风寒感冒", "寒湿"]},
            {"name": "无汗", "zheng": ["风寒感冒"]},
            {"name": "有汗", "zheng": ["风热感冒", "气虚"]},
            {"name": "咽喉肿痛", "zheng": ["风热感冒"]},
            {"name": "鼻塞流涕", "zheng": ["风寒感冒", "风热感冒"]},
            {"name": "咳嗽", "zheng": ["风寒感冒", "风热感冒", "痰湿"]},
            {"name": "咳痰", "zheng": ["痰湿"]},
            {"name": "神疲乏力", "zheng": ["气虚", "脾虚"]},
            {"name": "少气懒言", "zheng": ["气虚"]},
            {"name": "自汗", "zheng": ["气虚", "阳虚"]},
            {"name": "盗汗", "zheng": ["阴虚"]},
            {"name": "面色苍白", "zheng": ["血虚", "阳虚"]},
            {"name": "面色萎黄", "zheng": ["脾虚"]},
            {"name": "头晕眼花", "zheng": ["血虚", "肾虚"]},
            {"name": "心悸失眠", "zheng": ["血虚"]},
            {"name": "口干咽燥", "zheng": ["阴虚", "风热感冒"]},
            {"name": "潮热盗汗", "zheng": ["阴虚"]},
            {"name": "畏寒肢冷", "zheng": ["阳虚", "寒湿"]},
            {"name": "小便清长", "zheng": ["阳虚"]},
            {"name": "小便短黄", "zheng": ["湿热"]},
            {"name": "大便溏薄", "zheng": ["脾虚", "寒湿"]},
            {"name": "大便干结", "zheng": ["阴虚"]},
            {"name": "疼痛拒按", "zheng": ["血瘀"]},
            {"name": "胸闷腹胀", "zheng": ["痰湿", "气滞"]},
            {"name": "胸闷", "zheng": ["气滞", "肝郁气滞"]},
            {"name": "腹胀", "zheng": ["脾虚", "食积"]},
            {"name": "嗳气", "zheng": ["气滞", "食积"]},
            {"name": "易怒", "zheng": ["肝郁气滞", "气滞"]},
            {"name": "胁痛", "zheng": ["肝郁气滞"]},
            {"name": "腰膝酸软", "zheng": ["肾虚"]},
            {"name": "食欲不振", "zheng": ["脾虚", "食积"]},
            {"name": "口苦", "zheng": ["湿热"]},
            {"name": "嗳腐吞酸", "zheng": ["食积"]},
            {"name": "关节疼痛", "zheng": ["寒湿"]},
        ]
        for symptom in symptoms:
            cypher = """MERGE (s:症状 {name: $name})"""
            neo4j_conn.query(cypher, {"name": symptom["name"]})
            for zheng_name in symptom["zheng"]:
                cypher = """
                    MATCH (s:症状 {name: $symptom_name}), (z:证型 {name: $zheng_name})
                    MERGE (s)-[:属于]->(z)
                """
                neo4j_conn.query(cypher, {"symptom_name": symptom["name"], "zheng_name": zheng_name})

    @staticmethod
    def _init_tongue_signs():
        tongue_signs = [
            {"name": "舌苔薄白", "zheng": ["风寒感冒", "气虚"]},
            {"name": "舌苔薄黄", "zheng": ["风热感冒"]},
            {"name": "舌苔白腻", "zheng": ["痰湿", "寒湿"]},
            {"name": "舌苔黄腻", "zheng": ["湿热"]},
            {"name": "舌红", "zheng": ["风热感冒", "阴虚"]},
            {"name": "舌淡", "zheng": ["气虚", "血虚", "阳虚"]},
            {"name": "舌紫暗", "zheng": ["血瘀"]},
            {"name": "舌有齿痕", "zheng": ["脾虚", "痰湿"]},
            {"name": "舌红少苔", "zheng": ["阴虚"]},
            {"name": "舌苔厚腻", "zheng": ["食积"]},
        ]
        for tongue in tongue_signs:
            cypher = """MERGE (t:舌象 {name: $name})"""
            neo4j_conn.query(cypher, {"name": tongue["name"]})
            for zheng_name in tongue["zheng"]:
                cypher = """
                    MATCH (t:舌象 {name: $tongue_name}), (z:证型 {name: $zheng_name})
                    MERGE (t)-[:属于]->(z)
                """
                neo4j_conn.query(cypher, {"tongue_name": tongue["name"], "zheng_name": zheng_name})

    @staticmethod
    def _init_pulse_signs():
        pulse_signs = [
            {"name": "脉浮紧", "zheng": ["风寒感冒"]},
            {"name": "脉浮数", "zheng": ["风热感冒"]},
            {"name": "脉虚", "zheng": ["气虚"]},
            {"name": "脉细", "zheng": ["血虚"]},
            {"name": "脉细数", "zheng": ["阴虚"]},
            {"name": "脉沉迟", "zheng": ["阳虚"]},
            {"name": "脉涩", "zheng": ["血瘀"]},
            {"name": "脉滑", "zheng": ["痰湿"]},
            {"name": "脉弦", "zheng": ["气滞", "肝郁气滞"]},
            {"name": "脉濡缓", "zheng": ["寒湿"]},
            {"name": "脉沉细", "zheng": ["肾虚"]},
        ]
        for pulse in pulse_signs:
            cypher = """MERGE (p:脉象 {name: $name})"""
            neo4j_conn.query(cypher, {"name": pulse["name"]})
            for zheng_name in pulse["zheng"]:
                cypher = """
                    MATCH (p:脉象 {name: $pulse_name}), (z:证型 {name: $zheng_name})
                    MERGE (p)-[:属于]->(z)
                """
                neo4j_conn.query(cypher, {"pulse_name": pulse["name"], "zheng_name": zheng_name})

    @staticmethod
    def _init_herbs():
        herbs = [
            {
                "name": "麻黄", "pinyin": "mahuang", "property": "温", "flavor": "辛、微苦",
                "effect": "发汗解表，宣肺平喘，利水消肿",
                "dosage": "2-9g", "description": "麻黄科植物草麻黄、中麻黄或木贼麻黄的干燥草质茎",
                "meridians": ["手太阴肺经", "足太阳膀胱经"]
            },
            {
                "name": "桂枝", "pinyin": "guizhi", "property": "温", "flavor": "辛、甘",
                "effect": "发汗解肌，温通经脉，助阳化气",
                "dosage": "3-10g", "description": "樟科植物肉桂的干燥嫩枝",
                "meridians": ["手太阴肺经", "足太阳膀胱经", "手少阴心经"]
            },
            {
                "name": "生姜", "pinyin": "shengjiang", "property": "微温", "flavor": "辛",
                "effect": "解表散寒，温中止呕，化痰止咳",
                "dosage": "3-10g", "description": "姜科植物姜的新鲜根茎",
                "meridians": ["手太阴肺经", "足阳明胃经", "足太阴脾经"]
            },
            {
                "name": "连翘", "pinyin": "lianqiao", "property": "微寒", "flavor": "苦",
                "effect": "清热解毒，消肿散结",
                "dosage": "6-15g", "description": "木犀科植物连翘的干燥果实",
                "meridians": ["手太阴肺经", "手少阴心经", "手少阳三焦经"]
            },
            {
                "name": "金银花", "pinyin": "jinyinhua", "property": "寒", "flavor": "甘",
                "effect": "清热解毒，疏散风热",
                "dosage": "6-15g", "description": "忍冬科植物忍冬的干燥花蕾或带初开的花",
                "meridians": ["手太阴肺经", "手少阴心经", "足阳明胃经"]
            },
            {
                "name": "黄芪", "pinyin": "huangqi", "property": "微温", "flavor": "甘",
                "effect": "补气升阳，固表止汗，利水消肿",
                "dosage": "9-30g", "description": "豆科植物蒙古黄芪或膜荚黄芪的干燥根",
                "meridians": ["手太阴肺经", "足太阴脾经"]
            },
            {
                "name": "当归", "pinyin": "danggui", "property": "温", "flavor": "甘、辛",
                "effect": "补血活血，调经止痛，润肠通便",
                "dosage": "6-12g", "description": "伞形科植物当归的干燥根",
                "meridians": ["足太阴脾经", "足厥阴肝经", "手少阴心经"]
            },
            {
                "name": "川芎", "pinyin": "chuanxiong", "property": "温", "flavor": "辛",
                "effect": "活血行气，祛风止痛",
                "dosage": "3-10g", "description": "伞形科植物川芎的干燥根茎",
                "meridians": ["足厥阴肝经", "足少阳胆经", "手太阴肺经"]
            },
            {
                "name": "茯苓", "pinyin": "fuling", "property": "平", "flavor": "甘、淡",
                "effect": "利水渗湿，健脾，宁心",
                "dosage": "9-15g", "description": "多孔菌科真菌茯苓的干燥菌核",
                "meridians": ["手太阴肺经", "足太阴脾经", "足少阴肾经"]
            },
            {
                "name": "白术", "pinyin": "baizhu", "property": "温", "flavor": "甘、苦",
                "effect": "健脾益气，燥湿利水，止汗",
                "dosage": "6-12g", "description": "菊科植物白术的干燥根茎",
                "meridians": ["足太阴脾经", "足阳明胃经"]
            },
            {
                "name": "防风", "pinyin": "fangfeng", "property": "微温", "flavor": "辛、甘",
                "effect": "祛风解表，胜湿止痛，止痉",
                "dosage": "5-10g", "description": "伞形科植物防风的干燥根",
                "meridians": ["膀胱经", "肺经", "脾经", "肝经"]
            },
            {
                "name": "甘草", "pinyin": "gancao", "property": "平", "flavor": "甘",
                "effect": "益气补中，清热解毒，调和诸药",
                "dosage": "2-10g", "description": "豆科植物甘草、胀果甘草或光果甘草的干燥根和根茎",
                "meridians": ["心", "肺", "脾", "胃"]
            },
            {
                "name": "杏仁", "pinyin": "xingren", "property": "温", "flavor": "苦",
                "effect": "降气止咳平喘，润肠通便",
                "dosage": "5-10g", "description": "蔷薇科植物山杏、西伯利亚杏等的干燥成熟种子",
                "meridians": ["肺", "大肠"]
            },
            {
                "name": "薄荷", "pinyin": "bohe", "property": "凉", "flavor": "辛",
                "effect": "疏散风热，清利头目，利咽透疹",
                "dosage": "3-6g", "description": "唇形科植物薄荷的干燥地上部分",
                "meridians": ["肺", "肝"]
            },
            {
                "name": "荆芥", "pinyin": "jingjie", "property": "微温", "flavor": "辛",
                "effect": "解表散风，透疹，消疮",
                "dosage": "5-10g", "description": "唇形科植物荆芥的干燥地上部分",
                "meridians": ["肺", "肝"]
            },
            {
                "name": "白芍", "pinyin": "baishao", "property": "微寒", "flavor": "苦、酸",
                "effect": "养血调经，敛阴止汗，柔肝止痛",
                "dosage": "6-15g", "description": "毛茛科植物芍药的干燥根",
                "meridians": ["肝", "脾"]
            },
            {
                "name": "熟地黄", "pinyin": "shudihuang", "property": "微温", "flavor": "甘",
                "effect": "补血滋阴，益精填髓",
                "dosage": "9-15g", "description": "玄参科植物地黄的干燥块根",
                "meridians": ["肝", "肾"]
            },
            {
                "name": "桃仁", "pinyin": "taoren", "property": "平", "flavor": "苦、甘",
                "effect": "活血祛瘀，润肠通便",
                "dosage": "5-10g", "description": "蔷薇科植物桃或山桃的干燥成熟种子",
                "meridians": ["心", "肝", "大肠"]
            },
            {
                "name": "红花", "pinyin": "honghua", "property": "温", "flavor": "辛",
                "effect": "活血通经，散瘀止痛",
                "dosage": "3-10g", "description": "菊科植物红花的干燥花",
                "meridians": ["心", "肝"]
            },
            {
                "name": "生地黄", "pinyin": "shengdihuang", "property": "寒", "flavor": "甘、苦",
                "effect": "清热凉血，养阴生津",
                "dosage": "10-15g", "description": "玄参科植物地黄的新鲜或干燥块根",
                "meridians": ["心", "肝", "肾"]
            },
        ]
        for herb in herbs:
            cypher = """
                MERGE (h:中药 {name: $name, pinyin: $pinyin, property: $property, flavor: $flavor,
                               effect: $effect, dosage: $dosage, description: $description})
            """
            neo4j_conn.query(cypher, herb)
            for meridian in herb["meridians"]:
                cypher = """
                    MATCH (h:中药 {name: $herb_name}), (m:经络 {name: $meridian_name})
                    MERGE (h)-[:归经]->(m)
                """
                neo4j_conn.query(cypher, {"herb_name": herb["name"], "meridian_name": meridian})

    @staticmethod
    def _init_herb_compatibility():
        compatibility = [
            {"herb1": "麻黄", "herb2": "桂枝", "relation": "相须", "description": "增强发汗解表作用"},
            {"herb1": "黄芪", "herb2": "白术", "relation": "相须", "description": "增强健脾益气作用"},
            {"herb1": "当归", "herb2": "川芎", "relation": "相须", "description": "增强活血补血作用"},
            {"herb1": "茯苓", "herb2": "白术", "relation": "相须", "description": "增强健脾祛湿作用"},
            {"herb1": "金银花", "herb2": "连翘", "relation": "相须", "description": "增强清热解毒作用"},
            {"herb1": "麻黄", "herb2": "杏仁", "relation": "相使", "description": "麻黄宣肺，杏仁降气，协同平喘"},
            {"herb1": "甘草", "herb2": "麻黄", "relation": "相使", "description": "甘草缓和麻黄峻烈之性"},
        ]
        for comp in compatibility:
            cypher = """
                MATCH (h1:中药 {name: $herb1}), (h2:中药 {name: $herb2})
                MERGE (h1)-[:配伍 {relation: $relation, description: $description}]->(h2)
            """
            neo4j_conn.query(cypher, comp)

    @staticmethod
    def _init_herb_contraindications():
        contraindications = [
            {"herb": "麻黄", "content": "体虚多汗者慎用"},
            {"herb": "麻黄", "content": "高血压患者慎用"},
            {"herb": "桂枝", "content": "孕妇慎用"},
            {"herb": "红花", "content": "孕妇慎用"},
            {"herb": "桃仁", "content": "孕妇慎用"},
            {"herb": "杏仁", "content": "阴虚咳嗽者慎用"},
            {"herb": "生地黄", "content": "脾胃虚寒者慎用"},
        ]
        for contra in contraindications:
            cypher = """
                MATCH (h:中药 {name: $herb})
                MERGE (c:禁忌 {content: $content})
                MERGE (h)-[:禁忌]->(c)
            """
            neo4j_conn.query(cypher, contra)

    @staticmethod
    def _init_formulas():
        formulas = [
            {
                "name": "麻黄汤", "description": "发汗解表，宣肺平喘",
                "effect": "用于外感风寒表实证",
                "source": "《伤寒论》",
                "decoction_method": "水煎服",
                "herbs": ["麻黄", "桂枝", "杏仁", "甘草"],
                "zheng_types": ["风寒感冒"],
                "treatments": ["辛温解表"]
            },
            {
                "name": "桂枝汤", "description": "解肌发表，调和营卫",
                "effect": "用于外感风寒表虚证",
                "source": "《伤寒论》",
                "decoction_method": "水煎服，温覆取微汗",
                "herbs": ["桂枝", "芍药", "生姜", "大枣", "甘草"],
                "zheng_types": ["风寒感冒"],
                "treatments": ["辛温解表"]
            },
            {
                "name": "银翘散", "description": "辛凉解表，清热解毒",
                "effect": "用于外感风热表证",
                "source": "《温病条辨》",
                "decoction_method": "水煎服",
                "herbs": ["金银花", "连翘", "薄荷", "荆芥", "淡豆豉"],
                "zheng_types": ["风热感冒"],
                "treatments": ["辛凉解表"]
            },
            {
                "name": "玉屏风散", "description": "益气固表止汗",
                "effect": "用于表虚自汗",
                "source": "《丹溪心法》",
                "decoction_method": "水煎服",
                "herbs": ["黄芪", "白术", "防风"],
                "zheng_types": ["气虚"],
                "treatments": ["益气"]
            },
            {
                "name": "四物汤", "description": "补血调血",
                "effect": "用于血虚证",
                "source": "《仙授理伤续断秘方》",
                "decoction_method": "水煎服",
                "herbs": ["当归", "川芎", "白芍", "熟地黄"],
                "zheng_types": ["血虚"],
                "treatments": ["补血"]
            },
            {
                "name": "血府逐瘀汤", "description": "活血化瘀，行气止痛",
                "effect": "用于胸中血瘀证",
                "source": "《医林改错》",
                "decoction_method": "水煎服",
                "herbs": ["桃仁", "红花", "当归", "生地黄", "川芎"],
                "zheng_types": ["血瘀"],
                "treatments": ["活血化瘀"]
            },
            {
                "name": "补中益气汤", "description": "补中益气，升阳举陷",
                "effect": "用于脾胃气虚证，气虚下陷证",
                "source": "《脾胃论》",
                "decoction_method": "水煎服",
                "herbs": ["黄芪", "白术", "陈皮", "升麻", "柴胡"],
                "zheng_types": ["气虚", "脾虚"],
                "treatments": ["益气"]
            },
            {
                "name": "逍遥散", "description": "疏肝解郁，健脾养血",
                "effect": "用于肝郁脾虚证",
                "source": "《太平惠民和剂局方》",
                "decoction_method": "水煎服",
                "herbs": ["柴胡", "当归", "白芍", "白术", "茯苓"],
                "zheng_types": ["肝郁气滞", "脾虚"],
                "treatments": ["疏肝理气"]
            },
            {
                "name": "六味地黄丸", "description": "滋阴补肾",
                "effect": "用于肾阴不足证",
                "source": "《小儿药证直诀》",
                "decoction_method": "水煎服",
                "herbs": ["熟地黄", "山茱萸", "山药", "泽泻", "茯苓"],
                "zheng_types": ["阴虚", "肾虚"],
                "treatments": ["滋阴"]
            },
        ]
        for formula in formulas:
            cypher = """
                MERGE (f:方剂 {name: $name, description: $description, effect: $effect,
                               source: $source, decoction_method: $decoction_method})
            """
            neo4j_conn.query(cypher, formula)
            for herb in formula["herbs"]:
                cypher = """
                    MATCH (f:方剂 {name: $formula_name}), (h:中药 {name: $herb_name})
                    MERGE (f)-[:组成]->(h)
                """
                neo4j_conn.query(cypher, {"formula_name": formula["name"], "herb_name": herb})
            for zheng in formula["zheng_types"]:
                cypher = """
                    MATCH (f:方剂 {name: $formula_name}), (z:证型 {name: $zheng_name})
                    MERGE (f)-[:主治]->(z)
                """
                neo4j_conn.query(cypher, {"formula_name": formula["name"], "zheng_name": zheng})
            for treatment in formula.get("treatments", []):
                cypher = """
                    MATCH (f:方剂 {name: $formula_name}), (t:治法 {name: $treatment_name})
                    MERGE (f)-[:适用治法]->(t)
                """
                neo4j_conn.query(cypher, {"formula_name": formula["name"], "treatment_name": treatment})

    @staticmethod
    def _init_formula_modifications():
        modifications = [
            {"formula": "麻黄汤", "condition": "若喘甚", "modification": "加杏仁、苏子"},
            {"formula": "麻黄汤", "condition": "若头痛甚", "modification": "加川芎、白芷"},
            {"formula": "银翘散", "condition": "若咽喉肿痛甚", "modification": "加马勃、玄参"},
            {"formula": "银翘散", "condition": "若咳嗽甚", "modification": "加杏仁、桑叶"},
            {"formula": "玉屏风散", "condition": "若气虚甚", "modification": "加党参、炙甘草"},
            {"formula": "四物汤", "condition": "若血虚甚", "modification": "加黄芪、党参"},
            {"formula": "血府逐瘀汤", "condition": "若血瘀甚", "modification": "加三棱、莪术"},
        ]
        for mod in modifications:
            cypher = """
                MATCH (f:方剂 {name: $formula})
                MERGE (m:加减建议 {condition: $condition, modification: $modification})
                MERGE (f)-[:加减]->(m)
            """
            neo4j_conn.query(cypher, mod)

    @staticmethod
    def _init_medical_records():
        records = [
            {
                "title": "麻黄汤治疗风寒感冒案",
                "disease_name": "感冒",
                "zheng_type": "风寒感冒",
                "formula_name": "麻黄汤",
                "content": "患者恶寒发热，无汗头痛，身痛鼻塞，舌苔薄白，脉浮紧。辨证为风寒感冒，予麻黄汤加减治疗，服药三剂后症状缓解。",
                "author": "张仲景",
                "source": "《伤寒论》",
                "treatment_outcome": "治愈",
                "duration": "3天"
            },
            {
                "title": "银翘散治疗风热感冒案",
                "disease_name": "感冒",
                "zheng_type": "风热感冒",
                "formula_name": "银翘散",
                "content": "患者发热微恶风寒，有汗咽喉肿痛，口渴咳嗽，舌苔薄黄，脉浮数。辨证为风热感冒，予银翘散加减治疗。",
                "author": "吴鞠通",
                "source": "《温病条辨》",
                "treatment_outcome": "治愈",
                "duration": "3天"
            },
            {
                "title": "玉屏风散治疗气虚自汗案",
                "disease_name": "自汗",
                "zheng_type": "气虚",
                "formula_name": "玉屏风散",
                "content": "患者神疲乏力，少气懒言，自汗不止，动则加重，舌苔薄白，脉虚弱。辨证为气虚证，予玉屏风散加减治疗。",
                "author": "朱丹溪",
                "source": "《丹溪心法》",
                "treatment_outcome": "好转",
                "duration": "7天"
            },
            {
                "title": "四物汤治疗血虚眩晕案",
                "disease_name": "眩晕",
                "zheng_type": "血虚",
                "formula_name": "四物汤",
                "content": "患者面色苍白，头晕眼花，心悸失眠，肢体麻木，舌淡脉细。辨证为血虚证，予四物汤加黄芪、党参治疗。",
                "author": "陈自明",
                "source": "《妇人大全良方》",
                "treatment_outcome": "治愈",
                "duration": "14天"
            },
            {
                "title": "血府逐瘀汤治疗胸痛案",
                "disease_name": "胸痛",
                "zheng_type": "血瘀",
                "formula_name": "血府逐瘀汤",
                "content": "患者胸痛拒按，痛有定处，夜间加重，舌紫暗有瘀斑，脉涩。辨证为血瘀证，予血府逐瘀汤加减治疗。",
                "author": "王清任",
                "source": "《医林改错》",
                "treatment_outcome": "好转",
                "duration": "7天"
            },
            {
                "title": "补中益气汤治疗脾胃气虚案",
                "disease_name": "脾胃病",
                "zheng_type": "脾虚",
                "formula_name": "补中益气汤",
                "content": "患者食欲不振，腹胀便溏，神疲乏力，少气懒言，面色萎黄，舌淡脉弱。辨证为脾虚证，予补中益气汤治疗。",
                "author": "李东垣",
                "source": "《脾胃论》",
                "treatment_outcome": "治愈",
                "duration": "14天"
            },
            {
                "title": "逍遥散治疗肝郁脾虚案",
                "disease_name": "郁证",
                "zheng_type": "肝郁气滞",
                "formula_name": "逍遥散",
                "content": "患者胸闷胁痛，易怒善太息，食欲不振，腹胀便溏，舌苔薄白，脉弦。辨证为肝郁脾虚证，予逍遥散治疗。",
                "author": "严用和",
                "source": "《济生方》",
                "treatment_outcome": "好转",
                "duration": "10天"
            },
        ]
        for record in records:
            cypher = """
                MERGE (r:医案 {title: $title, disease_name: $disease_name,
                               zheng_type: $zheng_type, formula_name: $formula_name,
                               content: $content, author: $author, source: $source,
                               treatment_outcome: $treatment_outcome, duration: $duration})
            """
            neo4j_conn.query(cypher, record)


def init_knowledge_graph():
    print("Connecting to Neo4j...")
    neo4j_conn.connect()
    print("Creating schema constraints...")
    KnowledgeGraphInitializer.create_schema()
    print("Initializing basic data...")
    KnowledgeGraphInitializer.init_basic_data()
    print("Knowledge graph initialization completed!")


if __name__ == "__main__":
    init_knowledge_graph()
