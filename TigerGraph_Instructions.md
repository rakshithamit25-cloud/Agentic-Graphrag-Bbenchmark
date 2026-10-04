# TigerGraph Edge Loading and Testing Instructions

## Part 1: Loading `combined_edges.csv` via GraphStudio GUI

To load the combined CSV without hitting the 10-file limit, use the **Map Data To Graph** page in GraphStudio to map the single file to all 5 edge types using filters:

1. **Upload File:**
   - Go to **Map Data To Graph** on the left menu.
   - Click **Add data file** (the file icon with a plus) and upload `backend/data/combined_edges.csv`.
2. **Map to HAS_SYMPTOM:**
   - Click the data file, then click the `HAS_SYMPTOM` edge to create a mapping.
   - In the mapping panel on the right, click **Add Filter** (the funnel icon).
   - Set condition: Column `edge_type` `==` `"HAS_SYMPTOM"` (make sure to include quotes).
   - Map `from_id` to the Source vertex (`Animal`) and `to_id` to the Target vertex (`Symptom`).
3. **Map to Other Edges:**
   - Repeat step 2 for the other 4 edge types by clicking the *same* data file and mapping it to the target edge.
   - `HAS_TREATMENT` filter: `edge_type == "HAS_TREATMENT"`
   - `ASSOCIATED_WITH` filter: `edge_type == "ASSOCIATED_WITH"`
   - `AFFECTS` filter: `edge_type == "AFFECTS"`
   - `SUPERSEDES` filter: `edge_type == "SUPERSEDES"`
4. **Publish and Load:**
   - Click **Publish Data Mapping** (the up-arrow button on the toolbar).
   - Go to the **Load Data** page on the left menu.
   - Click **Start / Resume Loading** (Play button) to load the CSV. Wait for it to show 10 edges loaded.

*(Alternatively, if you prefer using GSQL shell, use the `create_loading_job.gsql` script provided in the backend folder).*

---

## Part 2: Verify Edge Counts
- Still on the **Load Data** screen, look at the **Graph Statistics** panel.
- Ensure the edge counts reflect the loaded rows (e.g., 3 `HAS_SYMPTOM`, 2 `HAS_TREATMENT`, 2 `ASSOCIATED_WITH`, 2 `AFFECTS`, 1 `SUPERSEDES`).

---

## Part 3: Test Multi-Hop Query

1. Go to the **Write Queries** page on the left menu.
2. Click **Add New GSQL Query** (plus icon) and name it `test_multi_hop`.
3. Paste the following query:

```gsql
CREATE QUERY test_multi_hop() FOR GRAPH AGRI_EVIDENCE { 
    // Start at Animal -> Symptom -> Disease -> Outbreak -> Market
    
    Start = {Animal.*};
    
    Step1_Symptoms = SELECT t FROM Start:s -(HAS_SYMPTOM:e)-> Symptom:t;
    PRINT Step1_Symptoms;
    
    Step2_Diseases = SELECT t FROM Step1_Symptoms:s -(INDICATES:e)-> Disease:t;
    PRINT Step2_Diseases;
    
    Step3_Outbreaks = SELECT t FROM Step2_Diseases:s -(ASSOCIATED_WITH:e)-> Outbreak:t;
    PRINT Step3_Outbreaks;
    
    Step4_Markets = SELECT t FROM Step3_Outbreaks:s -(AFFECTS:e)-> Market:t;
    PRINT Step4_Markets;
}
```
*Note: Make sure the edge from Symptom to Disease is correct in your schema (e.g., `INDICATES` per schema.gsql, or adjust if you used another edge type).*

4. Click **Save** then **Install Query** (the upload arrow icon).
5. Once installed, click **Run Query** (Play button) to verify the data flows properly through the graph.
