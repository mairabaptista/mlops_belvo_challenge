The component chosen for this part was the Orchestrated Experimentation Steps. Specifically, the demo involves **code** for only the data validation and data preparation steps due to time constraints. It involves creating an Airflow DAG, downloading the data from an s3 bucket, validating it using Pydantic and performing a simple processing step.
## Assumptions and Decisions
- The data validator took into consideration the dataset from the [Kaggle challenge](https://www.kaggle.com/datasets/sufyant/brazilian-real-bank-dataset)
- The dataset itself would be hard to deal with in a ML setting (for training), since it looks like an analysis dataset. If a more obvious feature column was present, it would be easier to perform model training.
- The problem stated "*At Belvo we enrich transaction data with transaction categories.*". The column `grupo_estabelecimento` looks like the categorization feature column. However, with the amount of different categories and the small dataset, it would be nearly impossible to produce a working model; more data points would be great to create a better performing model. 

### Running Instructions
```
docker-compose up --build -d
```
Interact with the Airflow cluster to run the DAG.