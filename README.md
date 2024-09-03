Enrihment Driven Graph Recommender- EDGAR

Explores pathway enrichment strategies in biomedical Knowledge Graphs (KGs) as a versatile link-prediction approach, with drug repurposing exemplifying a significant application. Leveraging systems biology, network expression analysis, pathway analysis (PA), and machine learning (ML) methods, KGs aid in uncovering novel interactions among biomedical entities of interest.
While these approaches excel in inferring missing edges within the KG, PA may overlook candidates with similar pathway effects.
By utilizing enrichment-driven analyses on KG data from ROBOKOP, our EDGAR paper applied this method on Alzheimer's disease case study, demonstrating the efficacy of enrichment strategies in linking entities for drug discovery. Our approach is validated through literature-based evidence derived from clinical trials, showcasing the potential of enrichment-driven strategies in linking biomedical entities.
s


## Demonstration
A Live version is available at: `https://edgar.apps.renci.org/`

## Local Development Steps
Clone the repo: `git clone  https://github.com/ranking-agent/edgar.git`

cd to the dir: `cd edgar`

Install requirements: `pip install -r requirements.txt`

on the terminal, run `python app.py`

## DEPLOYMENT

Build the Docker image: `docker build -t edgar:latest .`

Push the Docker image: `docker push edgar:latest`

