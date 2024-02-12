
![[Diagrama sem nome-Naive MLops.drawio 1.svg]]
*Figure 1.1*

The pipeline for the labeling problem is presented on figure 1.1. Since the given problem 
describes a fairly simple ML task (data analysis, running experiments, model training and batch inference), with no requirements for re-training, there is a clear separation of concerns between the ML-related tasks and the Operations related tasks. 
## High Level Overview
The raw data for analysis and experimentation is stored at a data store. Then, the ML Engineer (MLE)/Data Scientist (DS) perform an exploratory data analysis step. This is a manual step. Then, an experimentation step happens, where data is validated and prepared, followed by several iterations of model training and testing. All model iterations are saved to a model registry to ensure model tracking. Once the model passes certain quality quality criteria, it is eligible for production deployment. The code that produced the best model is versioned and packaged using continuous integration. Continuous deployment is the triggered, updating the model serving application with the required code. Inference happens once a day, on a set schedule, so new, unlabeled data is pulled from the data store and fed automatically to the inference pipeline. The same validation and preparation steps are performed and a batch prediction is made. The labeled data is finally stored in the data store.
# Components
## General Assumptions and Considerations
It is important to highlight some assumptions that justify the more general choices for this design.
- The pipeline(s) are hosted on AWS services. 
- The company already has a working Airflow cluster - Airflow was the chosen orchestrator, and due to its popularity, most data companies already have an Airflow cluster in place. Re-using a company's tech stack saves time for a MVP and reduces the learning curve. 
- Sagemaker was avoided - the whole architecture could have been done using Sagemaker. Although it is a very useful tool, it is costly. Using self managed services (EKS and EC2) is a cost saving solution (considering the extra time it takes to set up). Moreover, choosing to not rely heavily on Sagemaker avoids vendor lock-in.
- Unless stated otherwise, `boto3` is the choice of communication between AWS services. 
- [IAM](https://aws.amazon.com/iam/) and [VPC](https://aws.amazon.com/vpc/) setup is required but not detailed in this exercise. 
- Infrastructure setup is done through [Terraform](https://www.terraform.io/). 
## Data source
How the data arrives to the data source was not considered in this exercise. The raw data (as presented in the [Kaggle challenge](https://www.kaggle.com/datasets/sufyant/brazilian-real-bank-dataset)) is expected to be located at the data source before any pipeline run. The service choice is **AWS s3**. It is a cheap and reliable data lake solution and widely used and supported. The data located here is assumed to have been through a data quality step (perhaps using a tool like [Great Expectations](https://greatexpectations.io/)).
## Data Analysis
The data analysis step is assumed to be done offline by the MLE/DS using **Jupyter Notebooks**. This can be a local instance or even a cloud-based notebook instance. This is step should be very flexible to adapt to the MLE/DS needs.
## Orchestrated Experimentation Steps
Experimentation is a very iterative process; a MLE/DS is expected to try out different ML algorithms and parameters. Luckily, this process can be somewhat automatized. Airflow is the tool of choice for orchestrating these steps. Each DAG step is described below:
### Data validation
This is a important step to be performed, and [Pydantic](https://docs.pydantic.dev/latest/) was tool chosen for this exercise. Pydantic is widely used and supported. It offers the required type validations and modeling that are needed for the project. 
### Data Preparation
The data preparation step involves any data processing steps discovered through the data exploration stages. Additionally, different processing techniques can be done for different experiments: one experiment may have one-hot encoding of features, while another may not. [**Pandas**](https://pandas.pydata.org/) is a robust and widely used tool for processing. In this exercise we must be prepared for millions of files, but it is assumed that the files themselves aren't very large and the dataset used for training and testing can still be managed with Pandas. There are also strategies for working with [large datasets](https://pandas.pydata.org/docs/user_guide/scale.html) on Pandas. A possible evolution of this step is using [PySpark](https://spark.apache.org/docs/latest/api/python/index.html) if the workload is deemed too intense.
Data versioning is an interesting addition is this step. [DVC](https://dvc.org/) is the chosen tool for data versioning.
### Model Training, Evaluation and Validation
These steps can be "packaged" using [MLFlow](https://mlflow.org/). Its is a great tool with many functionalities. MLFlow can be easily integrated with Airflow by configuring run parameters. Since we're using MLFlow, a MLFlow server is there to track the experiments performed with Airflow. Each experiment results in a new model stored in the [MLFlow model registry](https://mlflow.org/docs/latest/model-registry.html), alongside its parameters.  The Model Registry is implemented with an [AWS RDS](https://aws.amazon.com/rds/) for simplification, but it could be spun with a managed DB solution. Per test definition: 

> Once a model passes certain quality criteria it can be deployed by the ML engineer into  
> production.

We can assume there are set quality criteria that were defined before any execution of the pipeline. This is an interesting assumption since it allows for further automation and helps in the CI/CD process. 
Using a conditional/branching DAG decorator we can pre-set the criteria the model will be tested against; if it performs well enough it can be upgraded to production status. If no models pass the quality test, an alarm can be raised for further inspection. Assuming a model was successful, its status on the Model Registry is changed and the pipeline can continue. 
The final step for the DAG at this stage is to automatically open a pull request to update model parameters with the newly discovered, best performing ones.
*As a side note, the MLE/DS can check [MLFlow Tracking](https://mlflow.org/docs/latest/tracking.html) to observe how each model performed.*
## CI/CD
As stated in the previous step, the best performing model parameters are then versioned to Github. The idea here is to create an automatic pull request with the model parameters. I believe that this PR should be approved  by a human, instead of being automatically merged. Following [trunk based development](https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development) principles, only a `development` and `main` branches should exist, to make CI easier. Through Github Actions, [CML](https://cml.dev/) can be introduced at this stage, making the comparison between current and new models easier. CML is a tool that can be integrated to a PR that showcases model performance. DVC can also be used here, alongside DVC to match data with model. 
Github Actions also aid with continuous deployment. On merge the serving pipeline can be updated to reflect any code changes during the data validation and preparation stages. It also updates the serving container on [AWS ECR](https://aws.amazon.com/ecr/).
## Automated Pipeline
At this point we enter the realm of model inference. Assumptions made at this stage:
- Inference must be done at a certain time, everyday.
- Incoming, unlabeled data is already at the correct s3 bucket. Previous steps are not considered in this exercise.
Inference orchestration will also be done using Airflow, which allows for precise scheduling. Each DAG step is described below:
### Data Extraction, Validation and Data Preparation
Assuming trunk based development best practices, at this stage the data validation and data preparation steps must match the ones in the `main` branch of our repository, which also reflects the best performing model created in the experimentation phase. The data extraction step merely fetches the incoming unlabeled data from the s3 bucket. 
### Prediction Service
In this design, the inference service is created using [AWS EKS](https://aws.amazon.com/eks/). This step could have been done with Sagemaker or AWS Batch; however, as before, I want to avoid vendor lock-in and extra costs. EKS is a great alternative for scalable solutions. Per test requirements:

> The whole process is part of other pipelines and should not take more than half an hour.

EKS easily allows for horizontal scaling whenever its required to meet this criteria. At this point the Airflow DAG will call on a `KubernetesPodOperator` to activate the inference service. At startup, the inference service uses the most recent ECR image to crate the inference pod. The inference pod pulls the production model from the MLFlow Model Registry Server. Then, with the aid of MLFlow, performs batch inference for the upcoming, prepared data. The fresh, labeled data is then uploaded to s3.
## Monitoring
A separate monitoring service is required to monitor the model's performance. [Evidently AI](https://www.evidentlyai.com/)'s tool is served on a separate instance (here we're using [EC2](https://aws.amazon.com/ec2/) as it is cheaper and easy to use). The application running on the EC2 instance shows a compilation of important metrics to model health, including data drift. The application can also send these metrics to a separate s3 bucket for further analysis. 
## Observability
[Datadog](https://www.datadoghq.com/) was the tool of choice for observability. Datadog agents can be added to the entire architecture, across both pipelines, as the agents for Airflow and EKS are very stable. This ensures greater control for the entire process and SLAs observation. 

