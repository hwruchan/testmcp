from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
import pandas as pd
import pymysql
from datetime import datetime
from zoneinfo import ZoneInfo

# FastMCP 서버 생성
mcp = FastMCP("smuchat")

# 기존 도구들
@mcp.tool()
def now_kr() -> dict:
    """
    Return current date/time info in Asia/Seoul (KST, UTC+9).
    """
    tz = ZoneInfo("Asia/Seoul")
    dt = datetime.now(tz)
    return {
        "iso": dt.isoformat(),
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M:%S"),
        "weekday": dt.strftime("%A"),
        "tz": "Asia/Seoul (KST, UTC+9)",
    }

@mcp.tool()
def query_smu_notices_by_keyword(keyword: str) -> dict:
    """
    'smu_notices' 테이블에서 'title' 컬럼에 특정 키워드를 포함하는 행을 조회하여 결과를 반환하는 도구.
    
    Args:
        keyword (str): 'title' 컬럼에서 찾을 키워드.
        
        dict: 키워드가 포함된 'title' 컬럼을 가진 행들 반환.
    """
    # DB 연결 설정
    DB_HOST = 'oneteam-db.chigywqq0qt3.ap-northeast-2.rds.amazonaws.com'
    DB_USER = 'admin'
    DB_PASSWORD = 'Oneteam2025!'
    DB_NAME = 'oneteam_DB'
    DB_PORT = 3306

    # MySQL 연결
    conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
    cursor = conn.cursor()

        # 쿼리 작성: 'title' 컬럼에서 키워드를 포함하는 행을 찾는 쿼리
    query = f"SELECT * FROM smu_notices WHERE title LIKE %s"
    cursor.execute(query, ('%' + keyword + '%',))
        
        # 결과를 DataFrame으로 변환
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(data, columns=column_names)

        # 결과 반환
    return df.to_dict(orient='records')
    
@mcp.tool()
def query_smu_meals_by_keyword(keyword: str) -> dict:
    """
    'smu_meals' 테이블에서 'meal' 컬럼과 'date' 컬럼에 특정 키워드를 포함하는 행을 조회하여 결과를 반환하는 도구.
    
    Args:
        keyword (str): 'meal' 컬럼과 'date' 컬럼에서 찾을 키워드. 예시: "오늘 점심"
        
        dict: 키워드가 포함된 'meal' 컬럼과 'date' 컬럼을 가진 행들 반환.
    """
    # DB 연결 설정
    DB_HOST = 'oneteam-db.chigywqq0qt3.ap-northeast-2.rds.amazonaws.com'
    DB_USER = 'admin'
    DB_PASSWORD = 'Oneteam2025!'
    DB_NAME = 'oneteam_DB'
    DB_PORT = 3306

    # MySQL 연결
    conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
    cursor = conn.cursor()

    # ----- 키워드에서 카테고리 잡기 -----
    category_code = None
    k = keyword.lower()
    if ("점심" in keyword) or ("런치" in keyword) or ("lunch" in k):
        category_code = "L"
    elif ("아침" in keyword) or ("조식" in keyword) or ("breakfast" in k):
        category_code = "B"

    # ----- 기본 쿼리 -----
    query = (
        "SELECT * FROM meal_menus "
        "WHERE (menu LIKE %s OR DATE_FORMAT(`date`, '%%Y-%%m-%%d') LIKE %s)"
    )
    params = [f"%{keyword}%", f"%{keyword}%"]

    # ----- 카테고리 조건 추가 -----
    if category_code:
        query += " AND category = %s"
        params.append(category_code)

    # 실행
    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(data, columns=column_names)

    return df.to_dict(orient="records")

# 데이터베이스와 통합된 기본 프롬프트
@mcp.prompt()
def default_prompt(message: str) -> list[base.Message]:
    tz = ZoneInfo("Asia/Seoul")
    now = datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    weekday_str = now.strftime("%A")

    return [
        base.AssistantMessage(
            "You are a smart agent with an ability to use tools. \n"
            "You will be given a question and you will use the tools to answer the question. \n"
            "Before answering any question that depends on dates or times, call the `now_kr` tool to confirm the current date/time in Asia/Seoul.\n"
             "When reasoning about any dates or times, you MUST anchor to the following clock:\n"
            f"- Today: {today_str} ({weekday_str}), Current time: {time_str}, Timezone: Asia/Seoul (KST, UTC+9).\n"
            "Interpret relative terms strictly as:\n"
            f"- 'today/오늘' = {today_str}\n"
            f"- 'yesterday/어제' = {(now.replace(hour=0, minute=0, second=0, microsecond=0)).date().fromordinal(now.date().toordinal()-1)}\n"
            f"- 'tomorrow/내일' = {(now.replace(hour=0, minute=0, second=0, microsecond=0)).date().fromordinal(now.date().toordinal()+1)}\n"
            "If the user does not specify a date, assume 'today'. Never use an internal or default model date.\n"
            "Pick the most relevant tool to answer the question. \n"
            "If you are failed to answer the question, try different tools to get context. \n"
            "When generating a response, if the data includes a URL or link, you must always provide it to the user. If there are multiple URLs, include all of them. \n"
            "Your answer should be very polite and professional."

        ),
        base.UserMessage(message),
    ]

# FastMCP 서버 실행
if __name__ == "__main__":
    mcp.run(transport="stdio")
