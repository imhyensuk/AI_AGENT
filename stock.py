import yfinance as yf
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

# 한글 종목명 → 티커 매핑 (필요시 확장)
TICKER_MAP = {
    "삼성전자": "005930.KS",
    "애플": "AAPL",
    # 필요시 추가
}

def guess_interval(query, interval):
    if interval:
        return interval
    if query:
        if "월" in query:
            return "1mo"
        if "주" in query:
            return "1wk"
        if "일" in query:
            return "1d"
    return "1d"

def get_close_series(data):
    # 멀티인덱스(예: KRX 종목) 처리
    if isinstance(data.columns, pd.MultiIndex):
        close_candidates = [col for col in data.columns if col[0] == 'Close']
        if close_candidates:
            return data[close_candidates[0]]
        else:
            raise ValueError("멀티인덱스에서 'Close' 컬럼을 찾을 수 없습니다.")
    else:
        return data['Close']

def get_col(data, col_name):
    # 멀티인덱스/단일인덱스 모두 지원
    if isinstance(data.columns, pd.MultiIndex):
        candidates = [col for col in data.columns if col[0] == col_name]
        if candidates:
            return data[candidates[0]]
        else:
            raise ValueError(f"멀티인덱스에서 '{col_name}' 컬럼을 찾을 수 없습니다.")
    else:
        return data[col_name]

def calculate_moving_average(data, window=5):
    close = get_close_series(data)
    return close.rolling(window=window).mean()

def calculate_rsi(data, window=14):
    close = get_close_series(data)
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

def run(
    query=None, ticker=None, start=None, end=None, interval=None,
    ma_window=5, rsi_window=14, summary=True, chart=True
):
    """
    ticker: 주식 티커 (예: AAPL, 005930.KS)
    start, end: 조회 기간 (YYYY-MM-DD)
    interval: '1d', '1wk', '1mo'
    ma_window: 이동평균선 기간
    rsi_window: RSI 계산 기간
    summary: 요약 통계 제공 여부
    chart: 차트 이미지(base64) 생성 여부
    """
    if not ticker and query:
        ticker = TICKER_MAP.get(query.strip(), query.strip().upper())
    if not ticker:
        return "주식 티커를 입력해 주세요. 예: AAPL, TSLA, 005930.KS"
    if not start:
        start = (datetime.now().replace(month=1, day=1)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    interval = guess_interval(query, interval)
    try:
        data = yf.download(ticker, start=start, end=end, interval=interval)
        if data.empty:
            return f"{ticker}에 대한 주가 데이터를 찾을 수 없습니다. (start={start}, end={end}, interval={interval})"
        ma = calculate_moving_average(data, ma_window)
        rsi = calculate_rsi(data, rsi_window)
        lines = []
        lines.append(f"{ticker} 주가 데이터 ({start} ~ {end}, 간격: {interval})")
        lines.append(f"이동평균선({ma_window}일) 및 RSI({rsi_window}일) 포함")
        lines.append("날짜 | 종가 | 이동평균선 | RSI | 거래량 | 시가 | 고가 | 저가")
        for idx, row in data.iterrows():
            date_str = idx.strftime('%Y-%m-%d')
            close = get_close_series(data).loc[idx]
            ma_val = ma.loc[idx]
            rsi_val = rsi.loc[idx]
            volume = get_col(data, 'Volume').loc[idx]
            open_p = get_col(data, 'Open').loc[idx]
            high = get_col(data, 'High').loc[idx]
            low = get_col(data, 'Low').loc[idx]
            close_str = f"{close:.2f}" if pd.notna(close) else "-"
            ma_str = f"{ma_val:.2f}" if pd.notna(ma_val) else "-"
            rsi_str = f"{rsi_val:.2f}" if pd.notna(rsi_val) else "-"
            volume_str = f"{int(volume)}" if pd.notna(volume) else "-"
            open_str = f"{open_p:.2f}" if pd.notna(open_p) else "-"
            high_str = f"{high:.2f}" if pd.notna(high) else "-"
            low_str = f"{low:.2f}" if pd.notna(low) else "-"
            lines.append(f"{date_str} | {close_str} | {ma_str} | {rsi_str} | {volume_str} | {open_str} | {high_str} | {low_str}")
        if summary:
            close_series = get_close_series(data)
            max_close = close_series.max()
            min_close = close_series.min()
            mean_close = close_series.mean()
            pct_change = ((close_series.iloc[-1] - close_series.iloc[0]) / close_series.iloc[0]) * 100 if len(close_series) > 1 else 0
            lines.append("")
            lines.append(f"요약: 최고가 {max_close:.2f}, 최저가 {min_close:.2f}, 평균가 {mean_close:.2f}, 기간 변동률 {pct_change:.2f}%")
        # 차트 생성
        chart_img = None
        if chart:
            close_series = get_close_series(data)
            fig, ax1 = plt.subplots(figsize=(10, 6))
            ax1.plot(data.index, close_series, label='종가', color='blue')
            ax1.plot(ma.index, ma, label=f'MA({ma_window})', color='orange')
            ax1.set_xlabel('날짜')
            ax1.set_ylabel('가격')
            ax1.legend(loc='upper left')
            ax2 = ax1.twinx()
            ax2.plot(rsi.index, rsi, label=f'RSI({rsi_window})', color='green')
            ax2.axhline(70, color='red', linestyle='--', linewidth=0.7)
            ax2.axhline(30, color='red', linestyle='--', linewidth=0.7)
            ax2.set_ylabel('RSI')
            ax2.legend(loc='upper right')
            plt.title(f'{ticker} 주가 및 기술적 지표')
            chart_img = plot_to_base64(fig)
        result_text = "\n".join(lines)
        if chart_img:
            result_text += f"\n\n[차트 이미지(base64)]: {chart_img}"
        return result_text
    except Exception as e:
        return f"주식 정보를 가져오는 중 오류 발생: {e}"
