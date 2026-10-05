import os
import json
import psycopg2

from groq import Groq
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

groq_client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

DB_URL=os.environ["SUPABASE_DB_URL"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/societies")
def get_societies_by_village(
    village: str = Query(..., min_length=1)
):
    db_url = DB_URL

    if not db_url:
        return {
            "error": "SUPABASE_DB_URL environment variable is not set"
        }

    conn = psycopg2.connect(db_url)

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                project_id,
                rera_id,
                district,
                taluka,
                village,
                project_name,
                registration_number,
                date_of_registration,
                proposed_completion_date,
                address,
                pincode,
                longitude,
                latitude,
                view_details_url,
                status
            FROM map_societies
            WHERE UPPER(TRIM(village)) = UPPER(TRIM(%s))
            ORDER BY project_name
        """, (village,))

        rows = cur.fetchall()

        columns = [
            "id",
            "project_id",
            "rera_id",
            "district",
            "taluka",
            "village",
            "project_name",
            "registration_number",
            "date_of_registration",
            "proposed_completion_date",
            "address",
            "pincode",
            "longitude",
            "latitude",
            "view_details_url",
            "status"
        ]

        result = [
            dict(zip(columns, row))
            for row in rows
        ]

        return {
            "village": village,
            "count": len(result),
            "societies": result
        }
    finally:
        conn.close()

@app.get("/home-search")
def home_search(location: str):

    db_url = DB_URL

    conn = psycopg2.connect(db_url)

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                UPPER(TRIM(village)) AS village,
                COUNT(*) AS society_count
            FROM map_societies
            WHERE
                village ILIKE %s
                OR address ILIKE %s
            GROUP BY UPPER(TRIM(village))
            ORDER BY
                CASE
                    WHEN UPPER(TRIM(village)) = UPPER(TRIM(%s))
                    THEN 0
                    ELSE 1
                END,
                society_count DESC
            LIMIT 1
        """, (
            "%" + location.strip() + "%",
            "%" + location.strip() + "%",
            location.strip()
        ))

        row = cur.fetchone()

        if not row:
            return {
                "location": location,
                "village": None,
                "count": 0,
                "societies": []
            }

        village = row[0]

        cur.execute("""
            SELECT
                id,
                project_id,
                rera_id,
                district,
                taluka,
                village,
                project_name,
                registration_number,
                date_of_registration,
                proposed_completion_date,
                address,
                pincode,
                longitude,
                latitude,
                view_details_url,
                status
            FROM map_societies
            WHERE UPPER(TRIM(village)) = UPPER(TRIM(%s))
            ORDER BY project_name
        """, (village,))

        rows = cur.fetchall()

        columns = [
            "id",
            "project_id",
            "rera_id",
            "district",
            "taluka",
            "village",
            "project_name",
            "registration_number",
            "date_of_registration",
            "proposed_completion_date",
            "address",
            "pincode",
            "longitude",
            "latitude",
            "view_details_url",
            "status"
        ]

        societies = [
            dict(zip(columns, row))
            for row in rows
        ]

        return {
            "location": location,
            "village": village,
            "count": len(societies),
            "societies": societies
        }

    finally:
        conn.close()


@app.post("/parse-home")
def parse_home_requirements(payload: dict):

    text = payload.get("text", "").strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="No requirement text provided"
        )

    try:

        response = groq_client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": """
You are a real-estate requirement extraction system.

Extract exactly these four fields:

1. location
2. bhk
3. budget
4. max_commute_minutes

Rules:

- location:
  Extract the locality, neighbourhood, area, workplace area,
  or city mentioned by the user.
  Example: Hinjewadi

- bhk:
  Extract number of bedrooms.
  "3 BHK" -> 3
  "2 bedroom" -> 2

- budget:
  Extract the numerical monthly rental budget.
  "30k" -> 30000
  "30 thousand" -> 30000
  "1 lakh" -> 100000
  "3000" -> 3000

  Do NOT change the user's number.

- max_commute_minutes:
  Extract maximum commute time.
  "not greater than 30 min" -> 30
  "within 45 minutes" -> 45
  "under 20 mins" -> 20

- If a field is not mentioned, return null.

Return ONLY valid JSON.
"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],

            response_format={
                "type": "json_object"
            },

            temperature=0
        )

        content = response.choices[0].message.content

        result = json.loads(content)

        return result

    except Exception as e:

        print("Groq error:", e)

        raise HTTPException(
            status_code=500,
            detail="Failed to extract home requirements"
        )