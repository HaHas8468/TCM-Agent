FROM node:20-alpine

WORKDIR /app

COPY traditional_medical_agent/neo4j_main/package.json traditional_medical_agent/neo4j_main/package-lock.json ./traditional_medical_agent/neo4j_main/
COPY traditional_medical_agent/neo4j_case/package.json traditional_medical_agent/neo4j_case/package-lock.json ./traditional_medical_agent/neo4j_case/
RUN npm ci --omit=dev --prefix traditional_medical_agent/neo4j_main \
    && npm ci --omit=dev --prefix traditional_medical_agent/neo4j_case

COPY traditional_medical_agent/neo4j_main/knowledge_graph_query.js ./traditional_medical_agent/neo4j_main/
COPY traditional_medical_agent/neo4j_case/neo4j_agent_api.js ./traditional_medical_agent/neo4j_case/
COPY knowledge_graph_service/server.js ./knowledge_graph_service/server.js

CMD ["node", "knowledge_graph_service/server.js"]
