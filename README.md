# Samsung Electronics Mock Auto Trader

한국투자증권 Open API의 **모의투자 REST API만** 사용하는 삼성전자(005930) 자동매매 과제입니다.

## Folder structure

```text
samsung_auto_trader/
├── main.py
├── config.py
├── auth.py
├── api_client.py
├── market_data.py
├── account.py
├── orders.py
├── trader.py
├── logger.py
├── token_cache.json
├── requirements.txt
├── .gitignore
└── README.md
```

## File responsibilities

- `main.py`: 프로그램 시작점
- `config.py`: 환경변수와 거래 설정
- `auth.py`: 토큰 발급 및 당일 토큰 재사용
- `api_client.py`: REST 요청, timeout, retry 처리
- `market_data.py`: 삼성전자 현재가 조회
- `account.py`: 계좌 잔고와 삼성전자 보유수량 조회
- `orders.py`: 모의투자 지정가 매수·매도
- `trader.py`: 거래시간, 폴링, 주문 및 체결 추정
- `logger.py`: 콘솔 및 파일 로그
- `token_cache.json`: 당일 access token 캐시

## Important design choices

- 모의투자 URL만 사용하며 실전투자 URL은 코드에 없습니다.
- WebSocket을 사용하지 않습니다.
- 당일 발급받은 토큰은 `token_cache.json`에서 재사용합니다.
- 모의투자의 낮은 요청 한도를 고려해 기본 주문 주기는 5분입니다.
- 각 사이클은 현재가 1회, 주문 전 잔고 1회만 조회합니다.
- 주문 후에는 체결 여부 추정을 위해 잔고를 한 번씩만 다시 조회합니다.
- 현금계좌에서 공매도를 가정하지 않으므로 보유수량이 없으면 매도 주문을 건너뜁니다.
- 교수님 프롬프트의 가격 차이가 ±2,000원과 ±1,000원으로 충돌하여, 기능 요구사항의 ±1,000원을 기본값으로 사용했습니다.

## 1. GitHub Codespaces secrets

GitHub의 **Settings → Codespaces → Secrets**에서 아래 값을 만듭니다.

```text
GH_ACCOUNT
GH_APPKEY
GH_APPSECRET
```

`GH_ACCOUNT`는 다음 중 하나로 저장할 수 있습니다.

```text
12345678-01
1234567801
12345678
```

8자리만 입력하면 계좌상품코드는 `01`로 처리합니다.

## 2. Install

```bash
pip install -r requirements.txt
```

## 3. Run

```bash
python main.py
```

프로그램은 한국 시간 기준 컴퓨터 시계가 `09:10` 이상이고 `15:30` 미만일 때만 주문 사이클을 수행합니다. `15:30` 이후에는 자동 종료합니다.

## 4. Change ±1,000 to ±2,000

`config.py`에서 아래 두 줄만 바꿉니다.

```python
buy_offset: int = 2_000
sell_offset: int = 2_000
```

## 5. API fields and transaction IDs

다음 값은 `config.py` 한곳에 모아 두었습니다.

```python
tr_id_current_price = "FHKST01010100"
tr_id_balance = "VTTC8434R"
tr_id_buy = "VTTC0802U"
tr_id_sell = "VTTC0801U"
```

한국투자증권의 API 개편 또는 계좌 조건에 따라 값이 달라지면 이 부분만 수정하면 됩니다.

잔고 응답의 가용현금 필드도 API 버전에 따라 다를 수 있으므로 `account.py`의 후보 필드를 한곳에 격리했습니다.

모의투자 환경에서 인증, 현재가 조회 및 계좌 잔고 조회까지 정상 작동을 확인하였다. 주문 기능도 구현하였으나 최종 실행 시점이 장 종료 이후여서 KIS 서버로부터 장 종료 응답을 받았으며, 실제 체결 기록은 생성되지 않았다.
