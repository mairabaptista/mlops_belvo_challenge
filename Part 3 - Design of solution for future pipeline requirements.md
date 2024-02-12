The pipeline in Part 1 can be change to accommodate the following requirements:

> - Predictions needed to be produced in real time (<1s per file)  
> - The model had to be retrained on a regular basis taking into account user feedback  
> - Different versions of the model could be trained and served on a self-served manner

Figure 3.1 shows a high level overview of this potential solution. 

![Figure 3.1](https://github.com/mairabaptista/mlops_belvo_challenge/assets/15002658/d9b5fc7b-fcd5-42dc-a67f-9c1780e9ba5d)
*Figure 3.1*
## High Level Overview
The raw data for analysis and experimentation is stored at a data store. Then, the ML Engineer (MLE)/Data Scientist (DS) perform an exploratory data analysis step. This is a manual step. Then, an experimentation step happens, where data is validated and prepared, followed by several iterations of model training and testing. Model analysis can be done at each iteration to gauge performance. However, since we're aiming for a higher level of automation, retraining must be done easily. This means that the code from the exploratory phase is versioned, updating the Automated Pipeline. This time, the Automated Pipeline is in charge of actually training and storing models in the Model Registry, allowing for automatically or manually triggered retrains. The model reaches an acceptable performance, it is upgraded to production. Another key point at this stage, we can easily leverage different model versions with this setup, which can be used later in different serving schemes. Again, the code that produced the best model is versioned and packaged using continuous integration. Continuous deployment is the triggered, updating the model serving application with the required code. According to the new requirements, each file goes through prediction separately, and prediction must be done at Near Real Time (NRT). Files are fed into the prediction service (after data validation and preparation), acting as a producer. Using a queue system, the data can be sent to consumer nodes (which do the active prediction) and then sent back to the producer for storage. Model performance can be tracked at NRT as well. 

# Components
## General Assumptions and Considerations
It is important to highlight some assumptions that justify the more general choices for this design.
- All the assumptions and considerations from  Part 1 still stand. 
- If a component is not described here, it means provides the exact same functionality and uses the exact same tools and services from Part 1.
## Orchestrated Experimentation Steps
### Model Training, Evaluation and Validation
In Part 1, the resulting models from these steps where logged in MLFlow Model Registry. This time this is not necessary, since the bulk of the training will be done at the Automated Pipeline stage. Training, Evaluation and Validation occur normally, however, the code is directly versioned to Github. 
## Continuous Integration
Using Github Actions we can update the automated pipeline using the code from the Orchestrated Experimentation Steps; the code is built and packaged, and necessary images are updated in ECR.
## Automated Pipeline
In this design, the automated pipeline concerns itself with the steps up until model validation. Assumptions made at this stage:
- Incoming, unlabeled data is already at the correct s3 bucket. Previous steps are not considered in this exercise.
Training orchestration will also be done using Airflow, which allows for precise scheduling. Each DAG step is described below:
### Data Extraction, Validation and Preparation
Again, we are assuming trunk based development best practices, at this stage the data validation and data preparation steps must match the ones in the `main` branch of our repository. The data extraction step merely fetches the incoming unlabeled data from the s3 bucket. 
### Model Training, Evaluation and Validation
The same setup from Part 1 (in Model Training, Evaluation and Validation) is used here, with MLFlow and Airflow. It is important to highlight that different model versions can be produced at this stage, and all are stored in the MLFlow Model Registry. 
## Model Serving
Through Github Actions, continuous deployment is easily achievable (for one or multiple models). For each model eligible for production, an EKS pod service is spun. The application inside the EKS pod is equipped with the appropriate data validation and preparation steps. A [SQS](https://aws.amazon.com/sqs/) queue is used to securely transport the data to be predicted. Any lost messages are sent to a DLQ, preventing data loss. A second EKS pod is used as a consumer, to effectively predict and store the results. EKS pods and SQS queues can be created programatically; therefore, this can be replicated to a number of models, and we can achieve the following requirement: 

> Different versions of the model could be trained and served on a self-served manner

## Performance Monitoring 
The labeled data is stored in the appropriate s3 bucket, which is also connected to the Performance monitoring service. It works the same as Part 1, using the same tools. The key difference here is that it is attached to a Trigger service.
### Trigger
The trigger is implemented as a Lambda Function. It has a simple functionality, and we can take advantage of the serverless compute for this stage. The Lambda Function automatically triggers the Airflow DAG in the Automated Pipeline stage for retraining, should the model degrade. As with ant Lambda Function, it can also be triggered manually, allowing for customization.
