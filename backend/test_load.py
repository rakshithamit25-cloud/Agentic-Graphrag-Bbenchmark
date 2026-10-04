import os
from pyTigerGraph import TigerGraphConnection
from config import Config

Config.validate()

conn = TigerGraphConnection(
    host=Config.TG_HOST,
    graphname=Config.TG_GRAPH_NAME,
    gsqlSecret=Config.TG_SECRET
)
conn.getToken(Config.TG_SECRET)

# Define the loading job
job_gsql = """
USE GRAPH AGRI_EVIDENCE
DROP JOB load_combined_edges
CREATE LOADING JOB load_combined_edges FOR GRAPH AGRI_EVIDENCE {
  DEFINE FILENAME f1;
  LOAD f1 TO EDGE HAS_SYMPTOM VALUES ($1, $2) WHERE $0 == "HAS_SYMPTOM" USING SEPARATOR=",", HEADER="true", EOL="\\n", QUOTE="double";
  LOAD f1 TO EDGE HAS_TREATMENT VALUES ($1, $2) WHERE $0 == "HAS_TREATMENT" USING SEPARATOR=",", HEADER="true", EOL="\\n", QUOTE="double";
  LOAD f1 TO EDGE ASSOCIATED_WITH VALUES ($1, $2) WHERE $0 == "ASSOCIATED_WITH" USING SEPARATOR=",", HEADER="true", EOL="\\n", QUOTE="double";
  LOAD f1 TO EDGE AFFECTS VALUES ($1, $2) WHERE $0 == "AFFECTS" USING SEPARATOR=",", HEADER="true", EOL="\\n", QUOTE="double";
  LOAD f1 TO EDGE SUPERSEDES VALUES ($1, $2) WHERE $0 == "SUPERSEDES" USING SEPARATOR=",", HEADER="true", EOL="\\n", QUOTE="double";
}
"""

print("Creating loading job...")
result = conn.gsql(job_gsql)
print("Create Loading Job Result:")
print(result)

csv_path = os.path.join(os.path.dirname(__file__), "data", "combined_edges.csv")

try:
    print(f"Uploading file {csv_path} and running loading job...")
    # Using REST API endpoint for file upload if runLoadingJobWithFile is available
    if hasattr(conn, 'runLoadingJobWithFile'):
        res = conn.runLoadingJobWithFile(
            filePath=csv_path,
            fileTag="f1",
            jobName="load_combined_edges"
        )
        print("Upload Result:", res)
    else:
        # Fallback if runLoadingJobWithFile is named differently or if we have to use the dataframe approach
        print("runLoadingJobWithFile not found, investigating available methods...")
        import pandas as pd
        df = pd.read_csv(csv_path)
        print("Available methods on conn:", [m for m in dir(conn) if 'load' in m.lower() or 'file' in m.lower()])
        # Actually pyTigerGraph uses `uploadFile` or `uploadFileByJob` for this, let's print dir
except Exception as e:
    print("Error during data load:", e)
