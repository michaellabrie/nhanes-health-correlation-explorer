# Prompt Log

## Prompt 1: Planning (plan mode)

I want to build a Streamlit application called `app.py` that allows users to explore correlations between different health measurements using the `nhanes_health.csv` dataset from the CDC's 2017–2018 NHANES survey.

Before doing anything, please examine the CSV file to understand its structure, column names, data types, and missing values. Do not write any code yet. I would like us to create and review a development plan before implementing the application.

The application should include five main features. First, a data preview with a short description of the dataset and an interactive table. Second, a pairwise correlation explorer where users can select two numerical variables using dropdown menus and view a scatter plot, correlation coefficient (r), and sample size (n). Include a trend line or binned means, along with an option to color points according to a health threshold, such as systolic blood pressure greater than or equal to 130 mmHg. Third, an interactive correlation heatmap where users can select which numerical variables to include. Every square should display the correlation coefficient and the number of complete observations used, with the color scale fixed from -1 to 1. Fourth, sidebar filters for sex and age range that update all displays and calculations throughout the application. Fifth, a selector that allows users to switch between Pearson and Spearman correlations in both the pairwise analysis and heatmap.

The numerical variables are age, bmi, waist_cm, systolic_bp, diastolic_bp, hba1c, total_chol, hdl_chol, sleep_hours, and sedentary_minutes. The sex column is categorical and should only be used for filtering, never included in correlation calculations.

All correlations must be calculated using the currently filtered dataset. Missing values should be excluded on a pairwise basis, so each correlation only uses participants with valid observations for both selected variables. The displayed sample size n must reflect the number of complete pairs used in that specific calculation, not simply the total number of filtered participants. Apply this same rule to the heatmap calculations. Clearly indicate when there is insufficient data to calculate a correlation.

The app should also explain that correlations do not establish causation, that a correlation near zero does not necessarily mean no relationship exists, and that these unweighted NHANES sample correlations should not automatically be generalized to the entire US population.

Use Python, Streamlit, pandas, and seaborn for the application. Keep the application in a single `app.py` file, load the dataset using the relative path `nhanes_health.csv`, and do not introduce other packages without asking me first.

Please provide a detailed but manageable development plan that explains the order in which you would implement the features, how the sidebar filters will feed into all calculations and visualizations, how missing values and correlation sample sizes will be handled, and how we will test the application. Include the command to run it locally and identify anything in my instructions that requires clarification.

Again, do not generate code or modify any files yet. I want to review and approve the plan first.

## Prompt 2: Build

Please proceed with implementing the approved development plan, beginning with loading the dataset and implementing the sidebar filters before adding the visualizations.

Make sure the approved development plan is saved in `plan.md` and my original prompt is recorded in `prompts.md`. Continue documenting my subsequent prompts.

Please implement all five required features in `app.py`, following the assignment instructions closely. Once implemented, help me run the application locally and identify anything that needs testing.

Do not complete the independent pandas verification on my behalf. I will run those calculations separately and document the results in `verification.md` after checking the values displayed by the app.

## Prompt 3: Prepare for submission and deployment

I have completed all six independent pandas verification checks, and every result matches the Streamlit app.

Please help me prepare the project for submission. Create `requirements.txt` with all required packages, including matplotlib, and verify that `app.py` loads `nhanes_health.csv` using a relative path.

Please review the six required submission files: `app.py`, `requirements.txt`, `nhanes_health.csv`, `prompts.md`, `plan.md`, and `verification.md`. Do not overwrite my independently recorded verification results.

Check for any remaining deployment issues, then guide me through publishing the project to a new public GitHub repository and deploying it on Streamlit Community Cloud.

Please do not publish anything until I approve the repository and deployment steps.

## Prompt 4: Git setup and publishing plan

Let's finish the NHANES website project now.

My GitHub username is michaellabrie, and I want the repository name to be nhanes-health-correlation-explorer.

Use Michael LaBrie as the commit author name. I want to use my GitHub noreply email address for commits, not my UF email. Please help me verify the correct noreply email before committing.

Do not include small_script.py in the published repository.

Please make sure the required published files are:
- app.py
- requirements.txt
- nhanes_health.csv
- prompts.md
- plan.md
- verification.md

Please also make sure verification.md keeps my completed verification results and includes the code check/documentation needed for the assignment.

Do not publish anything until I approve the steps. First, show me what files are ready and what commands you want to run for git setup and publishing.

## Prompt 5: Stage files for commit

Yes, please proceed with Step 1. Stage the required project files and show me the complete staged file list before creating the commit.

Please confirm that only the six required assignment files and `.gitignore` are included. Do not include `small_script.py`, temporary files, or cache folders.

Make sure my GitHub noreply email is configured for the commit. Once everything is ready, stop and ask for my approval before committing or pushing anything to GitHub.

## Prompt 6: Commit and prepare to publish

Yes, please proceed with creating the commit. Remove the optional "Co-Authored-By: Claude" line, since my use of Claude Code is already documented in prompts.md.

Keep Michael LaBrie as the commit author with my GitHub noreply email.

After the commit succeeds, please help me create the public GitHub repository named `nhanes-health-correlation-explorer` and push the committed files. Show me the publishing steps before executing them.

## Prompt 7: Connect to GitHub

I have created the empty public GitHub repository:

https://github.com/michaellabrie/nhanes-health-correlation-explorer

Please proceed with Step 3a to connect my local repository to GitHub. Show me the commands before pushing, and confirm that only the seven intended files will be published. Once I approve the push, verify that the repository is publicly accessible and that the main branch is correctly tracking origin/main.
