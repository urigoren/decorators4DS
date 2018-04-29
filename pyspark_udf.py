import pyspark.sql.functions as F
import pyspark.sql.types as T
from inspect import signature

"""
Goal:
    Translate python3 types to pyspark.sql.types
Usage:
     * All primitive types are mapped according to: https://github.com/apache/spark/blob/master/python/pyspark/sql/types.py#L890
     * [str] is mapped to ArrayType(StringType())
     * {str: int} is mapped to MapType(StringType(), IntegerType())
     * (int, str, bool) is mapped to a struct StructType(...)
     * Types can be constructed recursively, e.g. {int: [str]}
Example:
     * See parse_json_map function at the end of this file
"""


def _rec_build_types(t):
    if type(t) == list:
        return T.ArrayType(_rec_build_types(t[0]))
    elif type(t) == dict:
        k, v = list(t.items())[0]
        return T.MapType(_rec_build_types(k), _rec_build_types(v), True)
    elif type(t) == tuple:
        return T.StructType([T.StructField("v_" + str(i), _rec_build_types(f), True) for i, f in enumerate(t)])
    elif t in T._type_mappings:
        return T._type_mappings[t]()
    else:
        raise TypeError(repr(t) + " is not supported")


def udf(f):
    returnType = _rec_build_types(signature(f).return_annotation)
    return F.UserDefinedFunction(f, returnType)


if __name__ == "__main__":
    import json


    @udf
    def parse_json_map(s) -> {str: int}:
        return json.loads(s)


    spark.read.parquet("...").withColumn("json", parse_json_map)
