"""Generate 1M synthetic LLM-observability records in Spark and write Bronze.

The source rows are built with Spark expressions, rather than materialising a
million Python ``Row`` objects on the driver. This keeps the generator usable
alongside the notebook kernels in the Docker-sized local environment.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyspark.sql import functions as F

from spark_session import get_spark


DAYS_SPAN = 7


def main(n_rows: int = 1_000_000, out: str = "s3a://bronze/llm_calls_raw") -> None:
    spark = get_spark("generate_data")

    start_epoch = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    span_seconds = DAYS_SPAN * 24 * 3600
    row_id = F.col("id")
    bucket = F.pmod(row_id * F.lit(17) + F.lit(11), F.lit(10))

    model = (
        F.when(bucket < 6, F.lit("claude-sonnet-4-6"))
        .when(bucket < 9, F.lit("claude-haiku-4-5"))
        .otherwise(F.lit("claude-opus-4-7"))
    )
    prompt_tokens = F.pmod(row_id * F.lit(7919) + F.lit(53), F.lit(3951)) + F.lit(50)
    completion_tokens = F.pmod(row_id * F.lit(3571) + F.lit(29), F.lit(1981)) + F.lit(20)
    latency_ms = F.greatest(
        F.lit(50),
        F.when(model == "claude-haiku-4-5", completion_tokens * F.lit(0.56) + F.lit(450))
        .when(model == "claude-sonnet-4-6", completion_tokens * F.lit(1.38) + F.lit(1100))
        .otherwise(completion_tokens * F.lit(3.0) + F.lit(2400)),
    ).cast("int")
    status_bucket = F.pmod(row_id * F.lit(13) + F.lit(7), F.lit(100))
    status = (
        F.when(status_bucket < 95, F.lit("ok"))
        .when(status_bucket < 98, F.lit("rate_limited"))
        .otherwise(F.lit("error"))
    )

    # Every twentieth row repeats the preceding request ID: exactly 5% retry
    # rows (apart from the first row), which makes Silver dedup observable.
    request_num = F.when(row_id % 20 == 0, row_id - 1).otherwise(row_id)
    df = (
        spark.range(n_rows, numPartitions=16)
        .select(
            F.concat(F.lit("req_"), request_num).alias("request_id"),
            F.timestamp_seconds(
                F.lit(start_epoch) + (row_id * F.lit(span_seconds) / F.lit(n_rows)).cast("long")
            ).alias("ts"),
            F.to_json(
                F.struct(
                    model.alias("model"),
                    F.concat(F.lit("u_"), F.pmod(row_id, F.lit(5000))).alias("user_id"),
                    F.struct(
                        prompt_tokens.alias("input"),
                        completion_tokens.alias("output"),
                    ).alias("usage"),
                    latency_ms.alias("latency_ms"),
                    status.alias("status"),
                )
            ).alias("raw_json"),
        )
    )

    df.write.format("delta").mode("overwrite").save(out)
    expected_duplicates = n_rows // 20
    print(
        f"Wrote {n_rows:,} rows to {out}\n"
        f"  expected duplicate request_ids: ~{expected_duplicates:,}\n"
        f"  date span: {DAYS_SPAN} UTC days from 2026-04-01"
    )
    spark.stop()


if __name__ == "__main__":
    main()
