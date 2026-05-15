# Stock Telegram Alert

เครื่องมือแจ้งเตือนหุ้นผ่าน Telegram โดยดึงราคาจาก Yahoo Finance, วิเคราะห์กราฟด้วย technical indicators พื้นฐาน และดึงข่าวล่าสุดของแต่ละ ticker เพื่อช่วยให้เห็นหุ้นที่ควรจับตามองเร็วขึ้น

> ข้อมูลนี้เป็นเครื่องมือช่วยติดตาม ไม่ใช่คำแนะนำการลงทุน ต้องตรวจสอบข่าว งบการเงิน ความเสี่ยง และแผนลงทุนของตัวเองก่อนตัดสินใจเสมอ

## สิ่งที่ระบบทำ

- ดึงราคาย้อนหลังของหุ้นใน watchlist
- วิเคราะห์แนวโน้มด้วย SMA, RSI, MACD, ADX, ATR, Bollinger position, volume และ breakout
- ดึงข่าวล่าสุดต่อ ticker จาก Yahoo Finance RSS
- สรุปข่าวและประเมิน tone ข่าวแบบโปร่งใสจากคำสำคัญในหัวข้อ/summary
- จัดอันดับด้วย opportunity score หลังรวม technical score และ news tone
- สรุปว่าแต่ละบริษัททำธุรกิจอะไรจากไฟล์ config ที่ผู้ใช้กำหนดเอง
- ให้คะแนน signal แบบโปร่งใส พร้อมเหตุผลว่าทำไมควรจับตา
- ส่ง Telegram เป็น digest จัดอันดับเฉพาะตัวที่ score ถึง threshold
- ลดโอกาสโดน news rate limit โดยวิเคราะห์กราฟและจัดอันดับก่อน แล้วค่อยดึงข่าวเฉพาะหุ้น top list

## ติดตั้ง

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
cp config/watchlist.example.json config/watchlist.json
```

แก้ `.env`:

```bash
TELEGRAM_BOT_TOKEN=ใส่ token จาก BotFather
TELEGRAM_CHAT_ID=ใส่ chat id ของคุณ
STOCK_WATCHLIST=PTT.BK,AOT.BK,NVDA
```

หรือใช้ `config/watchlist.json` เพื่อใส่ชื่อบริษัทและธุรกิจให้ละเอียดขึ้น

## ใช้รายชื่อหุ้นจำนวนมาก

ไม่ควรใส่หุ้นทุกตัวลง `STOCK_WATCHLIST=` โดยตรง เพราะ env var จะยาวมาก ดูแลยาก และอาจทำให้ระบบยิง request หลายพันตัวในรอบเดียว

ถ้าต้องการสแกน universe กว้าง ๆ ให้ใช้:

```bash
STOCK_WATCHLIST=ALL
STOCK_UNIVERSE=US
MAX_SYMBOLS_PER_RUN=0
TOP_ALERTS_PER_RUN=0
MAX_NEWS_LOOKUPS_PER_RUN=50
```

รายละเอียด:

- `US` ดึงรายชื่อหุ้นจาก Nasdaq Trader symbol directory และกรอง ETF/test issue ออก
- Universe US จะกรอง preferred, warrant, unit, right และ instrument ที่ไม่ใช่ common stock ออก เพื่อลด ticker ที่ Yahoo ไม่มีราคา
- ถ้าต้องการรวมไทยด้วย ให้ตั้ง `STOCK_UNIVERSE=US,TH` และสร้างไฟล์ `config/universe.th.csv` ก่อน
- `TH` โหลดจากไฟล์ `config/universe.th.csv` โดยต้องมี columns `ticker,name,business`
- ใช้ `config/universe.th.example.csv` เป็นตัวอย่าง แล้วสร้าง `config/universe.th.csv` สำหรับรายชื่อจริง
- `MAX_SYMBOLS_PER_RUN=0` คือไม่จำกัดจำนวนหุ้น ถ้าใส่เลขมากกว่า 0 จะเป็น safety cap กัน runtime ยาวและ provider rate limit
- `TOP_ALERTS_PER_RUN=0` ส่งทุกตัวที่เข้าเกณฑ์ ถ้าใส่เลขมากกว่า 0 จะจำกัดจำนวนต่อรอบ
- ระบบแบ่ง Telegram digest เป็นชุดละ 10 ตัว เพื่อไม่ให้ข้อความยาวเกิน
- ข่าวจะถูกดึงเฉพาะหุ้นที่ผ่าน ranking แล้ว ไม่ดึงข่าวทุกตัวใน universe
- Digest จะติด tag เช่น `🚀 น่าสนใจมาก`, `🔥 ข่าวบวกแรง`, `⚠️ ข่าวลบแรง`, `📈 trend แข็งแรง`
- `MAX_NEWS_LOOKUPS_PER_RUN` จำกัดจำนวนหุ้นที่ไปดึงข่าวต่อรอบหลังผ่าน technical filter เพื่อลดการโดน Yahoo rate limit

ตัวอย่างไฟล์ `config/universe.th.csv`:

```csv
ticker,name,business
PTT,PTT,Energy and petroleum business
AOT,Airports of Thailand,Airport operator
ADVANC,Advanced Info Service,Telecommunications
```

ระบบจะเติม `.BK` ให้อัตโนมัติสำหรับ ticker ไทยที่ยังไม่มี suffix

## รันทันทีหนึ่งรอบ

แบบคำสั่งเดียว:

```bash
./scripts/run_once.sh
```

หรือรันตรงผ่าน Python:

```bash
python -m stock_alerts run-once --watchlist config/watchlist.json
```

## รันแบบเฝ้าดูต่อเนื่อง

แบบคำสั่งเดียว:

```bash
./scripts/watch.sh
```

ถ้า `.env` ตั้ง `STOCK_WATCHLIST=ALL` script จะไม่ใช้ `config/watchlist.json` แม้ไฟล์นี้จะมีอยู่ และจะสแกน universe ตาม `STOCK_UNIVERSE`

หรือรันตรงผ่าน Python:

```bash
python -m stock_alerts watch --watchlist config/watchlist.json
```

## ตรวจคุณภาพ

```bash
ruff check .
pytest
```

## ข้อควรระวัง

- อย่า commit `.env` เพราะมี Telegram token
- ถ้าข่าวไม่ขึ้น อาจเป็นข้อจำกัดของ Yahoo Finance RSS หรือ ticker ไม่รองรับ
- Technical signal ไม่ได้ทำนายอนาคต เป็นเพียงตัวช่วยกรองหุ้นที่ควรตรวจต่อ
- ระบบจะไม่ฟันธงว่า “ขึ้นแน่” หรือ “กำไร 100-200%” แต่จะช่วยจัดอันดับ candidate ที่ควรศึกษาต่อจากราคา, momentum, volume และข่าว

## Research-backed scoring notes

ระบบใช้ technical indicators ที่เป็นมาตรฐานในงาน technical analysis เช่น RSI, MACD, ADX, ATR และ Bollinger Bands เพื่อแยก trend, momentum, volatility และ breakout ออกจากกัน

ข้อจำกัดที่ต้องรู้:

- Indicator ไม่ใช่เครื่องทำนายอนาคต ต้องใช้ร่วมกับข่าว งบการเงิน valuation และ risk management
- News tone ตอนนี้เป็น keyword heuristic เพื่อความเบาและโปร่งใส ไม่ใช่โมเดล sentiment ขั้นสูง
- ถ้าต้องการ news sentiment ที่จริงจังกว่านี้ ควรเพิ่มโหมด FinBERT หรือ LLM-based financial sentiment ในรอบถัดไป
