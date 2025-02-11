from groq import Groq
import json
import os
from rpy2.robjects import r, default_converter
from rpy2.robjects.conversion import localconverter

# Initialize the Groq client 
client = Groq()

answerer_prompt = """
You are an expert statistician and data scientist that specializes in answering homework questions.
Assume all necessary text files are downloaded at /Users/samueltownsend/Desktop/UCI/Winter_2025/R_class/Homework/HW<homework_number>/<filename>.txt
and when writing R code, make sure to read in the data and assume there is a header (header=True).
Not all files will need to write R code, so only write code when it's explicitly stated that there is a file in the question context.
You will be provided with a list of available data files to you - do not write any code that includes files not listed in the available files.
You can infer the homework number from the given input.
In your output, rewrite each question with the answer right below it.
"""


# Define models
ROUTING_MODEL = "llama3-70b-8192"
TOOL_USE_MODEL = "llama-3.3-70b-versatile"
GENERAL_MODEL = "llama3-70b-8192"

def execute_r(extracted_r_code):
    """Tool to run r code"""
    with localconverter(default_converter):
        try:
            original_dir = os.getcwd()
            r(f'setwd("{os.path.abspath("R_images")}")')
            r('options(device="png")')
            # Execute R code
            result = r(extracted_r_code)
            r(f'setwd("{original_dir}")')
            return result

        except Exception as e:
            return str(e)

def route_query(query):
    """Routing logic to let LLM decide if tools are needed"""
    routing_prompt = f"""
    Given the following user query, determine if any tools are needed to answer it.
    If an r execution tool is needed, respond with 'TOOL: EXECUTE_R'.
    If no tools are needed, respond with 'NO TOOL'.

    User query: {query}

    Response:
    """
    
    response = client.chat.completions.create(
        model=ROUTING_MODEL,
        messages=[
            {"role": "system", "content": "You are a routing assistant. Determine if tools are needed based on the user query."},
            {"role": "user", "content": routing_prompt}
        ],
        max_completion_tokens=20  # We only need a short response
    )
    
    routing_decision = response.choices[0].message.content.strip()
    
    if "TOOL: EXECUTE_R" in routing_decision:
        return "execute_r"
    else:
        return "no tool needed"

def run_with_tool(query):
    """Use the tool use model to perform the calculation"""
    messages = [
        {
            "role": "system",
            "content": "You are a R code executor assistant. Use the execute_r function to run the code and provide the results.",
        },
        {
            "role": "user",
            "content": query,
        }
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "execute_r",
                "description": "Run some r code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "extracted_r_code": {
                            "type": "string",
                            "description": "The R code to execute",
                        }
                    },
                    "required": ["extracted_r_code"],
                },
            },
        }
    ]
    response = client.chat.completions.create(
        model=TOOL_USE_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_completion_tokens=4096
    )
    print(response)
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    if tool_calls:
        messages.append(response_message)
        for tool_call in tool_calls:
            function_args = json.loads(tool_call.function.arguments)
            function_response = execute_r(function_args.get("extracted_r_code"))
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "execute_r",
                    "content": function_response,
                }
            )
        second_response = client.chat.completions.create(
            model=TOOL_USE_MODEL,
            messages=messages
        )
        return second_response.choices[0].message.content
    return response_message.content

def run_general(query):
    """Use the general model to answer the query since no tool is needed"""
    response = client.chat.completions.create(
        model=GENERAL_MODEL,
        messages=[
            {"role": "system", "content": answerer_prompt},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content

def process_query(query):
    """Process the query and route it to the appropriate model"""
    route = route_query(query)
    if route == "execute_r":
        response = run_with_tool(query)
    else:
        response = run_general(query)
    
    return {
        "query": query,
        "route": route,
        "response": response
    }

# Example usage
if __name__ == "__main__":
    queries = [
        "Say we want a multiple linear regression model with all the covariates listed in it, along with an interaction between height and weight. Write out this population model.",
        "Why does it make sense to have an interaction between weight and height in the model? Explain.",
        "Fit the model from part a. in R and write out the estimated model. What is the adjusted R-squared value?",
        "What is the estimated SSE (sum of squared errors) of your model? Use the R output from the summary(model), along with some formulas, to compute this.",
        "Test if your model has any significance. Write out the null and alternative hypothesis, the test statistic (and what distribution it follows), p-value, and make a conclusion.",
        "Test the interaction term between height and weight. State the null and alternative hypothesis and p-value. What can you conclude with respect to the effect of height and weight on the response of resting heart rate?",
        "Now a researcher states that you do not need weight in the model in any way or form. Write out the null and alternative hypothesis for this (write it out in terms of slope coefficients).",
        "Conduct the test from part g. Make a conclusion in context of the study.",
        "Show the output from R for the sequential sum of regressions table (keep the order of X1, X2, X3, and X1X2 in your model). Does adding weight when height is already in the model add to the explanatory strength of the model?",
        "Using the sequential sum of regression table from part i, what is the SSTO (sum of squared total) for this model?",
        "Now say you have a model with only height in it. From your table in part i, what is the SSE, SSR, and SSTO of this model with only height as covariate? Note: Do not run a new model, use the table from part i.",
        "Explain in a few sentences how daily exercise amount could be a potential confounder in the model from part a.",
        "Using the model from part a., create and present the scatterplot of the residual versus fitted values (fitted values go on the X-axis).",
        "Is there any evidence that our assumption of constant variance (a single sigma2 for the entire model) is invalid?",
        "Using the residual vs. fitted plot from part m., comment on the linearity assumption of the model that was fit.",
        "Using the model from part a., now create a QQ plot of the residuals. Do we seem to have any issues with our normality assumption for the errors?",
        "Using the model from part a., do a summary(data) to see the summary statistics of the weight (Wgt) explanatory variable. Does it make sense to use your model from part a. to predict the resting heart rate for someone who weighs 350 pounds? Why or why not.",
        ]
    
    for query in queries:
        result = process_query(query)
        print(f"Query: {result['query']}")
        print(f"Route: {result['route']}")
        print(f"Response: {result['response']}\n")