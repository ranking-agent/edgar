Enrihment Driven Graph Recommender- EDGAR

Explores pathway enrichment strategies in biomedical Knowledge Graphs (KGs) as a versatile link-prediction approach, with drug repurposing exemplifying a significant application. Leveraging systems biology, network expression analysis, pathway analysis (PA), and machine learning (ML) methods, KGs aid in uncovering novel interactions among biomedical entities of interest.
While these approaches excel in inferring missing edges within the KG, PA may overlook candidates with similar pathway effects.
By utilizing enrichment-driven analyses on KG data from ROBOKOP, this study focuses on repurposing drug candidates for Alzheimer's disease, demonstrating the efficacy of enrichment strategies in linking entities for drug discovery. Our approach is validated through literature-based evidence derived from clinical trials, showcasing the potential of enrichment-driven strategies in linking biomedical entities.

AUTHORS: Chris Bizon

email address: cbizon@renci.org

website: https://www.renci.org

company name: Renaissance Computing Institute
address: 100 Europa Drive, Durham, NC.

HOW TO RUN

## LOCALLY
Clone the repo: `git clone  https://github.com/ranking-agent/edgar.git`

cd to the dir: `cd edgar`

Install requirements: `pip install -r requirements.txt`


## DEPLOYMENT

Build the Docker image: `docker build -t edgar:latest .`

Push the Docker image: `docker push edgar:latest`

## Live version

`https://edgar.apps.renci.org/`