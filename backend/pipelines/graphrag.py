import sys
import os

# Ensure the backend directory is in the path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We try to import Config, catching ValueError if environment variables like TG_HOST are missing.
try:
    from config import Config
except Exception as e:
    Config = None
    CONFIG_ERROR = f"{str(e)}. Please ensure environment variables like TG_HOST are set and dependencies like python-dotenv are installed."
else:
    CONFIG_ERROR = None

class GraphRAGPipeline:
    def __init__(self):
        self.conn = None
        self.error = None
        
        if CONFIG_ERROR:
            self.error = f"Configuration missing: {CONFIG_ERROR}"
            return

        try:
            from pyTigerGraph import TigerGraphConnection
            self.conn = TigerGraphConnection(
                host=Config.TG_HOST,
                graphname=Config.TG_GRAPH_NAME,
                gsqlSecret=Config.TG_SECRET,
                apiToken=Config.TG_API_TOKEN,
                username=Config.TG_USERNAME,
                password=Config.TG_PASSWORD
            )
            if Config.TG_SECRET:
                self.conn.getToken(Config.TG_SECRET)
        except ImportError:
            self.error = "pyTigerGraph package is not installed."
        except Exception as e:
            self.error = f"Failed to initialize TigerGraph connection: {str(e)}"

    def retrieve_context(self, query: str = None) -> dict:
        """
        Retrieves the connected Disease, Treatment, Outbreak, and Market 
        information from TigerGraph as structured Python data.
        """
        if self.error:
            return {
                "status": "error",
                "message": self.error,
                "data": None
            }

        if not self.conn:
            return {
                "status": "error",
                "message": "Database connection is not established.",
                "data": None
            }

        try:
            # Fetch the vertices for the relevant connected components as structured data
            diseases = self.conn.getVertices("Disease")
            treatments = self.conn.getVertices("Treatment")
            outbreaks = self.conn.getVertices("Outbreak")
            markets = self.conn.getVertices("Market")

            return {
                "status": "success",
                "message": "Successfully retrieved GraphRAG context.",
                "data": {
                    "diseases": diseases,
                    "treatments": treatments,
                    "outbreaks": outbreaks,
                    "markets": markets
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error during data retrieval: {str(e)}",
                "data": None
            }

def run_graphrag_pipeline(query: str = None) -> dict:
    pipeline = GraphRAGPipeline()
    return pipeline.retrieve_context(query)

if __name__ == "__main__":
    # Test the pipeline
    result = run_graphrag_pipeline()
    import json
    print(json.dumps(result, indent=2))
