# Useful Decorators for Data Science

  
## PySpark

  1. `pyspark_udf` - Coverts python3 type hints into PySpark return types and return `PySparkUDF` object.
  
## sklearn
  1. `sktransform` - Turn any function into an sklearn Transformaer, and use it in an sklearn Pipeline.
  
## Caching

  1. `json_file` - Save function calls to a json file.
  1. `pickle_file` - Save function calls to a pickle file.
  1. `s3_cache` - Save function calls to amazon s3.
  
## Regression Tests
  1. `regres.record` - Record funcion inputs and outputs.
  1. `regres.replay` - Replay recorded data against a different implementation.
  
## Logging
  1. `log_error` - Logs errors using the `logging` module.
  1. `slack_error` - Sends a slack message when an error occurs.
  
  
## Time
  1. `time_limit` - Limit execution time to `s` seconds.

## SSH connection
  1. `ssh_connect` - Run python code on a remote SSH Server.
