from flask import Flask, render_template, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

ETF_DATA = {
    'XLK': {
        'name': 'Technology Select Sector SPDR Fund',
        'full_name': 'テクノロジー株', 'en_full_name': 'Technology Stocks',
        'sector': 'Technology', 'quadrant': 'top-left', 'ticker': 'XLK',
        'expense_ratio': '0.10%',
        'description': 'S&P500のテクノロジーセクター企業に投資するETF。半導体、ソフトウェア、IT機器・サービス企業を幅広くカバー。',
        'en_description': 'S&P 500 technology sector ETF covering semiconductors, software, and IT hardware & services companies.',
        'strong_in': '景気拡大局面（強い経済）と低金利環境で最もパフォーマンスが高い。低金利は成長株の将来キャッシュフローの現在価値を高め、強い経済は企業・消費者のテクノロジー支出を増やす。',
        'en_strong_in': 'Best in strong economy + low rate expansion. Low rates boost growth stock valuations; strong GDP drives corporate and consumer tech spending.',
        'weak_in': '高金利環境では割引率上昇により成長株のバリュエーションが圧縮されやすい。',
        'en_weak_in': 'Rising rates compress growth stock valuations by increasing the discount rate applied to future earnings.',
        'top_holdings': ['Apple (AAPL)', 'Microsoft (MSFT)', 'NVIDIA (NVDA)', 'Broadcom (AVGO)', 'Salesforce (CRM)'],
    },
    'VGT': {
        'name': 'Vanguard Information Technology ETF',
        'full_name': 'テクノロジー株（バンガード）', 'en_full_name': 'Technology Stocks (Vanguard)',
        'sector': 'Technology', 'quadrant': 'top-left', 'ticker': 'VGT',
        'expense_ratio': '0.10%',
        'description': 'バンガード社のITセクターETF。XLKよりも広い範囲のテクノロジー企業をカバーし、中小型株も含む。',
        'en_description': "Vanguard's IT sector ETF with broader coverage than XLK, including small and mid-cap tech companies.",
        'strong_in': 'XLKと同様に強い経済・低金利環境で優位。より分散されたポートフォリオで中小型テック企業の成長も取り込める。',
        'en_strong_in': 'Same drivers as XLK with added upside from smaller-cap tech in low-rate expansion environments.',
        'weak_in': '高金利・景気後退局面では特に小型成長株の影響を受けやすい。',
        'en_weak_in': 'More exposed than XLK to small-cap growth selloffs in rising rate environments.',
        'top_holdings': ['Apple (AAPL)', 'Microsoft (MSFT)', 'NVIDIA (NVDA)', 'Broadcom (AVGO)', 'Meta (META)'],
    },
    'XLF': {
        'name': 'Financial Select Sector SPDR Fund',
        'full_name': '金融株', 'en_full_name': 'Financial Stocks',
        'sector': 'Financials', 'quadrant': 'top-left', 'ticker': 'XLF',
        'expense_ratio': '0.10%',
        'description': '銀行、保険、証券など金融セクター全般に投資するETF。景気の健全さを反映した動きをする。',
        'en_description': 'Banks, insurance, brokerage, and other financial companies. Closely tracks overall economic health.',
        'strong_in': '強い経済環境では融資需要増加・不良債権減少で収益が改善。やや金利が上昇し始める局面（Strong Economy移行期）でも利ざや改善で恩恵を受ける。',
        'en_strong_in': 'Strong economies reduce loan defaults and boost lending demand. Early rate-hike phases improve net interest margins.',
        'weak_in': '景気後退局面では不良債権増加・融資縮小で大きく下落するリスクがある。',
        'en_weak_in': 'Recessions spike defaults and contract lending, causing sharp earnings declines.',
        'top_holdings': ['Berkshire Hathaway (BRK.B)', 'JPMorgan Chase (JPM)', 'Visa (V)', 'Mastercard (MA)', 'Bank of America (BAC)'],
    },
    'XLI': {
        'name': 'Industrial Select Sector SPDR Fund',
        'full_name': '工業株', 'en_full_name': 'Industrial Stocks',
        'sector': 'Industrials', 'quadrant': 'top-right', 'ticker': 'XLI',
        'expense_ratio': '0.10%',
        'description': '航空宇宙・防衛、機械、輸送、建設など工業セクターに投資するETF。景気サイクルの後半（ピーク）で特に強い。',
        'en_description': 'Aerospace & defense, machinery, transportation, and construction companies. Strongest in the late economic cycle.',
        'strong_in': '強い経済下では設備投資増加・インフラ需要拡大で恩恵。高インフレ期には製品価格への転嫁能力が高く、実物資産ベースのビジネスが強み。',
        'en_strong_in': 'Capital expenditures surge during expansion. Inflationary late-cycle environments reward the pricing power of physical asset-based businesses.',
        'weak_in': '景気後退では設備投資が急減し大幅下落するリスク。',
        'en_weak_in': 'Capital expenditure collapses in recessions, causing significant drawdowns across the sector.',
        'top_holdings': ['GE Aerospace (GE)', 'Caterpillar (CAT)', 'Honeywell (HON)', 'Union Pacific (UNP)', 'Boeing (BA)'],
    },
    'XLB': {
        'name': 'Materials Select Sector SPDR Fund',
        'full_name': '素材株', 'en_full_name': 'Materials Stocks',
        'sector': 'Materials', 'quadrant': 'top-right', 'ticker': 'XLB',
        'expense_ratio': '0.10%',
        'description': '化学、金属・採掘、建設材料、紙・林産物などの素材セクターETF。コモディティ価格と密接に連動。',
        'en_description': 'Chemicals, metals & mining, construction materials, and paper/forestry companies. Closely tied to commodity prices.',
        'strong_in': '景気拡大局面での需要増加とインフレによるコモディティ価格上昇の両方から恩恵。インフレヘッジとしての役割も大きい。',
        'en_strong_in': 'Benefits from increased demand during expansion AND commodity price inflation. Serves as an effective inflation hedge.',
        'weak_in': '景気後退・デフレ環境ではコモディティ需要・価格ともに下落し大きく調整。',
        'en_weak_in': 'Both demand and commodity prices fall in deflationary recessions, amplifying losses.',
        'top_holdings': ['Linde (LIN)', 'Sherwin-Williams (SHW)', 'Air Products (APD)', 'Freeport-McMoRan (FCX)', 'Ecolab (ECL)'],
    },
    'XLY': {
        'name': 'Consumer Discretionary Select Sector SPDR Fund',
        'full_name': '一般消費財株', 'en_full_name': 'Consumer Cyclical Stocks',
        'sector': 'Consumer Discretionary', 'quadrant': 'top-right', 'ticker': 'XLY',
        'expense_ratio': '0.10%',
        'description': '自動車、小売、ホテル・レストラン、娯楽などの一般消費財セクターETF。消費者信頼感と可処分所得に敏感。',
        'en_description': 'Auto makers, retailers, hotels & restaurants, and entertainment. Highly sensitive to consumer confidence and disposable income.',
        'strong_in': '強い経済下で雇用増加・賃金上昇により消費者の裁量支出が増える。景気拡大の恩恵を直接受ける。',
        'en_strong_in': 'Job growth and rising wages in a strong economy directly expand consumer discretionary purchasing power.',
        'weak_in': '景気後退・高インフレ環境では消費者が裁量支出を削減するため大幅下落。',
        'en_weak_in': 'Discretionary spending is the first to be cut when the economy weakens or inflation rises.',
        'top_holdings': ['Amazon (AMZN)', 'Tesla (TSLA)', "McDonald's (MCD)", 'Home Depot (HD)', 'Nike (NKE)'],
    },
    'VOX': {
        'name': 'Communication Services Select Sector SPDR Fund',
        'full_name': '通信株', 'en_full_name': 'Communication Services',
        'sector': 'Communication Services', 'quadrant': 'bottom-left', 'ticker': 'VOX',
        'expense_ratio': '0.10%',
        'description': 'テレコム、メディア、エンターテインメント、インターネットなど通信サービスセクターのETF（Vanguard版）。',
        'en_description': 'Telecom, media, entertainment, and internet companies (Vanguard). A mix of defensive and growth characteristics.',
        'strong_in': '低金利・景気後退期には防衛的な通信インフラ事業が底堅い。ストリーミングサービスなど不況時も需要が安定しているビジネスモデルを多く含む。',
        'en_strong_in': 'Defensive telecom infrastructure stays resilient in downturns. Streaming services maintain stable demand even in recessions.',
        'weak_in': '高金利環境ではメディア企業の負債コスト増加で苦戦する場合がある。',
        'en_weak_in': 'High-debt media companies face elevated interest costs in high-rate environments.',
        'top_holdings': ['Meta Platforms (META)', 'Alphabet (GOOGL)', 'Netflix (NFLX)', 'T-Mobile (TMUS)', 'Verizon (VZ)'],
    },
    'XLV': {
        'name': 'Health Care Select Sector SPDR Fund',
        'full_name': 'ヘルスケア株', 'en_full_name': 'Healthcare Stocks',
        'sector': 'Health Care', 'quadrant': 'bottom-left', 'ticker': 'XLV',
        'expense_ratio': '0.10%',
        'description': '製薬、医療機器、ヘルスケアサービス、バイオテクノロジーなど医療セクター全般のETF。',
        'en_description': 'Pharmaceuticals, medical devices, healthcare services, and biotech. One of the most defensive sectors in the S&P 500.',
        'strong_in': '景気に左右されにくいディフェンシブセクター。景気後退・低金利局面で相対的に強い。医療需要は景気循環に依存しない構造的成長。',
        'en_strong_in': 'Largely immune to economic cycles. Healthcare demand grows structurally regardless of economic conditions.',
        'weak_in': '薬価規制リスクや規制変更で大きく動く場合がある。景気拡大局面では市場全体に出遅れやすい。',
        'en_weak_in': 'Drug pricing regulation risk can trigger sharp sector-wide selloffs. Lags the broad market in strong bull runs.',
        'top_holdings': ['Johnson & Johnson (JNJ)', 'UnitedHealth (UNH)', 'Eli Lilly (LLY)', 'AbbVie (ABBV)', 'Pfizer (PFE)'],
    },
    'XLP': {
        'name': 'Consumer Staples Select Sector SPDR Fund',
        'full_name': '生活必需品株', 'en_full_name': 'Consumer Defensive Stocks',
        'sector': 'Consumer Staples', 'quadrant': 'bottom-left', 'ticker': 'XLP',
        'expense_ratio': '0.10%',
        'description': '食料品、飲料、タバコ、日用品など生活必需品セクターのETF。景気に最も左右されないディフェンシブセクター。',
        'en_description': 'Food & beverage, tobacco, household products, and personal care companies. The most defensive sector in the S&P 500.',
        'strong_in': '景気後退・不確実性の高い局面で最もディフェンシブ。消費者は不況でも食料・日用品の消費を削れないため安定収益を維持。配当利回りも高め。',
        'en_strong_in': "Consumers can't cut food and daily essentials even in a recession. Stable earnings and above-average dividends.",
        'weak_in': '景気拡大局面では成長株に比べてパフォーマンスが大幅に劣後しやすい。',
        'en_weak_in': 'Significantly underperforms growth sectors during economic expansions.',
        'top_holdings': ['Procter & Gamble (PG)', 'Coca-Cola (KO)', 'PepsiCo (PEP)', 'Costco (COST)', 'Walmart (WMT)'],
    },
    'XLU': {
        'name': 'Utilities Select Sector SPDR Fund',
        'full_name': '公益事業株', 'en_full_name': 'Utilities Stocks',
        'sector': 'Utilities', 'quadrant': 'bottom-left', 'ticker': 'XLU',
        'expense_ratio': '0.10%',
        'description': '電力、ガス、水道などの公益事業セクターETF。安定した配当を提供する債券的な性質を持つ。',
        'en_description': 'Electric, gas, and water utilities. Bond-like nature with stable high dividends from regulated monopoly businesses.',
        'strong_in': '低金利・景気後退局面で債券の代替として買われる。規制された独占的ビジネスで安定収益・高配当。',
        'en_strong_in': 'Acts as a bond proxy in low-rate downturns. Regulated monopolies deliver stable earnings and high dividends.',
        'weak_in': '高金利環境では債券との競争で売られやすく、高い負債コストが収益を圧迫する。',
        'en_weak_in': 'Rate hikes make bonds more attractive and significantly increase utility companies\' debt costs.',
        'top_holdings': ['NextEra Energy (NEE)', 'Southern Company (SO)', 'Duke Energy (DUK)', 'Sempra Energy (SRE)', 'American Electric (AEP)'],
    },
    'XLE': {
        'name': 'Energy Select Sector SPDR Fund',
        'full_name': 'エネルギー株', 'en_full_name': 'Energy Stocks',
        'sector': 'Energy', 'quadrant': 'bottom-right', 'ticker': 'XLE',
        'expense_ratio': '0.10%',
        'description': '石油・ガスの探査・生産・精製・配送企業に投資するETF。原油・天然ガス価格と高い相関。',
        'en_description': 'Oil & gas exploration, production, refining, and distribution. Tightly correlated with crude oil and natural gas prices.',
        'strong_in': 'インフレ・高金利環境（コモディティ価格上昇期）で強い。地政学的リスクや供給制約による原油価格上昇で大きく恩恵。',
        'en_strong_in': 'Surges with commodity price inflation and supply constraints. Geopolitical risk premiums also boost energy stocks.',
        'weak_in': '景気後退による需要減少や原油価格急落時に大幅下落。',
        'en_weak_in': 'Demand destruction from a weakening economy and oil price collapses cause major drawdowns.',
        'top_holdings': ['ExxonMobil (XOM)', 'Chevron (CVX)', 'ConocoPhillips (COP)', 'EOG Resources (EOG)', 'Schlumberger (SLB)'],
    },
    'VTI': {
        'name': 'Vanguard Total Stock Market ETF',
        'full_name': '米国全株式市場', 'en_full_name': 'US Total Stock Market',
        'sector': 'Total Market', 'quadrant': 'center', 'ticker': 'VTI',
        'expense_ratio': '0.03%',
        'description': '米国株式市場全体（大型・中型・小型株約4,000銘柄以上）に分散投資するETF。最低コストで市場全体に投資できる。',
        'en_description': 'Broadest US equity exposure — ~4,000+ stocks across large, mid, and small cap. The foundation of a diversified portfolio at minimal cost.',
        'strong_in': 'あらゆる経済環境で長期的に最も安定した資産形成ツール。市場全体の平均リターンを低コストで得られる。長期投資の基本。',
        'en_strong_in': 'Delivers full market returns in all economic environments through complete diversification. Beats most active managers long-term.',
        'weak_in': '特定セクターがアウトパフォームする局面では劣後する。ただし長期では多くのアクティブ運用を上回る実績。',
        'en_weak_in': 'Underperforms specific outperforming sectors during strong directional markets, but outpaces most active strategies over the long run.',
        'top_holdings': ['Apple (AAPL)', 'Microsoft (MSFT)', 'NVIDIA (NVDA)', 'Amazon (AMZN)', 'Meta (META)'],
    },
}

QUADRANT_INFO = {
    'top-left': {
        'name': '景気拡大・低金利', 'en_name': 'Expansion + Low Rates',
        'description': 'FRBが緩和的な金融政策を維持しつつ経済が成長している段階。グロース株・テクノロジー株が最も恩恵を受ける。',
        'en_description': 'The Fed maintains accommodative policy while the economy grows. Growth and technology stocks benefit the most.',
        'color': '#5cb85c', 'etfs': ['XLK', 'VGT', 'XLF'],
    },
    'top-right': {
        'name': '景気拡大・高金利', 'en_name': 'Expansion + High Rates',
        'description': 'インフレ対応でFRBが利上げしているが経済は依然堅調な段階。景気後半サイクルで実物資産・コモディティ関連が強い。',
        'en_description': 'The Fed raises rates to combat inflation, but the economy remains resilient. Late-cycle physical assets and commodities lead.',
        'color': '#5bc0de', 'etfs': ['XLI', 'XLB', 'XLY'],
    },
    'bottom-left': {
        'name': '景気後退・低金利', 'en_name': 'Recession + Low Rates',
        'description': 'FRBが利下げし景気支援に動いているが経済が弱い段階。ディフェンシブセクターが相対的に強い。',
        'en_description': 'The Fed cuts rates to support a weakening economy. Defensive sectors outperform on a relative basis.',
        'color': '#e91e8c', 'etfs': ['VOX', 'XLV', 'XLP', 'XLU'],
    },
    'bottom-right': {
        'name': '景気後退・高金利', 'en_name': 'Recession + High Rates',
        'description': 'スタグフレーション的な環境。景気は弱いがインフレが続き金利が高止まり。エネルギーなどコモディティが相対的に底堅い。',
        'en_description': 'Stagflationary environment — weak economy with persistent inflation. Energy and commodities provide relative resilience.',
        'color': '#f0ad4e', 'etfs': ['XLE'],
    },
}


def fetch_fred_series(series_id, limit=13):
    if not FRED_API_KEY:
        return None
    try:
        url = (f"{FRED_BASE}?series_id={series_id}&api_key={FRED_API_KEY}"
               f"&file_type=json&sort_order=desc&limit={limit}")
        resp = requests.get(url, timeout=10)
        data = resp.json()
        obs = data.get('observations', [])
        return [o for o in obs if o.get('value') != '.']
    except Exception as e:
        print(f"FRED error ({series_id}): {e}")
        return None


def get_yfinance_rate():
    try:
        import yfinance as yf
        irx = yf.Ticker('^IRX')
        hist = irx.history(period='5d')
        if not hist.empty:
            return round(float(hist['Close'].iloc[-1]), 2)
    except Exception:
        pass
    return None


def determine_phase(fed_rate, gdp_growth, cpi_yoy):
    economy_strong = None
    rates_high = None
    if gdp_growth is not None:
        economy_strong = gdp_growth > 2.0
    if fed_rate is not None:
        rates_high = fed_rate > 2.5
    if economy_strong is None or rates_high is None:
        if rates_high is not None:
            return ('top-right' if rates_high else 'top-left', 'low')
        return ('unknown', 'none')
    if economy_strong and not rates_high:
        return ('top-left', 'high')
    elif economy_strong and rates_high:
        return ('top-right', 'high')
    elif not economy_strong and not rates_high:
        return ('bottom-left', 'high')
    else:
        return ('bottom-right', 'high')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/etf-data')
def etf_data():
    return jsonify(ETF_DATA)


@app.route('/api/economic-phase')
def economic_phase():
    indicators = {
        'fed_rate': None, 'fed_rate_date': None, 'fed_rate_source': None,
        'gdp_growth': None, 'gdp_date': None,
        'cpi_yoy': None, 'cpi_date': None,
        'has_fred_key': bool(FRED_API_KEY),
        'timestamp': datetime.now().isoformat(),
    }
    yf_rate = get_yfinance_rate()
    if yf_rate is not None:
        indicators['fed_rate'] = yf_rate
        indicators['fed_rate_source'] = 'Yahoo Finance (^IRX 3ヶ月T-bill)'
    if FRED_API_KEY:
        fed_data = fetch_fred_series('FEDFUNDS', limit=1)
        if fed_data:
            indicators['fed_rate'] = float(fed_data[0]['value'])
            indicators['fed_rate_date'] = fed_data[0]['date']
            indicators['fed_rate_source'] = 'FRED (Federal Funds Rate)'
        gdp_data = fetch_fred_series('A191RL1Q225SBEA', limit=1)
        if gdp_data:
            indicators['gdp_growth'] = float(gdp_data[0]['value'])
            indicators['gdp_date'] = gdp_data[0]['date']
        cpi_data = fetch_fred_series('CPIAUCSL', limit=13)
        if cpi_data and len(cpi_data) >= 13:
            current = float(cpi_data[0]['value'])
            year_ago = float(cpi_data[12]['value'])
            indicators['cpi_yoy'] = round((current / year_ago - 1) * 100, 2)
            indicators['cpi_date'] = cpi_data[0]['date']
    phase, confidence = determine_phase(
        indicators.get('fed_rate'), indicators.get('gdp_growth'), indicators.get('cpi_yoy'))
    phase_etfs = QUADRANT_INFO[phase]['etfs'] if phase in QUADRANT_INFO else []
    return jsonify({
        'phase': phase, 'confidence': confidence,
        'phase_info': QUADRANT_INFO.get(phase),
        'phase_etfs': phase_etfs,
        'indicators': indicators,
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
