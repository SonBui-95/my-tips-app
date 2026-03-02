import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="My Tips Dashboard", layout="wide")
st.title("📊 Báo Cáo Tiền Tips Theo Tháng")

# --- KẾT NỐI DỮ LIỆU ---
@st.cache_data(ttl=600)
def load_data():
    try:
        # 1. Tạo credentials từ secrets.toml
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )

        # 2. Authorize với gspread
        client = gspread.authorize(creds)

        # 3. Mở Google Sheet
        sheet = client.open("tips_received").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        # 4. Xử lý dữ liệu
        if not df.empty and 'Ngày' in df.columns:
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True, errors='coerce')
            df['Tháng/Năm'] = df['Ngày'].dt.strftime('%m/%Y')

        return df

    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

# --- LOAD DATA ---
df = load_data()

if not df.empty:

    df = df.dropna(subset=["Ngày"])

    # --- GROUP THEO THÁNG ---
    df['Sort_Period'] = df['Ngày'].dt.to_period('M')

    df_monthly = (
        df.groupby(['Sort_Period', 'Tháng/Năm'])['Tiền Tips']
        .sum()
        .reset_index()
        .sort_values('Sort_Period')
    )

    st.subheader("🗓️ Tổng hợp thu nhập theo tháng")

    cols = st.columns(len(df_monthly))
    for index, row in df_monthly.iterrows():
        with cols[index]:
            st.metric(
                label=f"Tháng {row['Tháng/Năm']}",
                value=f"{row['Tiền Tips']:,.0f} VNĐ"
            )

    st.divider()

    # --- BIỂU ĐỒ ---
    st.subheader("📊 Biểu đồ so sánh thu nhập các tháng")

    fig_col = px.bar(
        df_monthly,
        x='Tháng/Năm',
        y='Tiền Tips',
        text_auto=',.0f',
        color='Tiền Tips',
        color_continuous_scale='Viridis',
        title="Tổng tiền Tips theo tháng"
    )

    fig_col.update_layout(
        xaxis={'categoryorder': 'array',
               'categoryarray': df_monthly['Tháng/Năm']}
    )

    st.plotly_chart(fig_col, use_container_width=True)

    with st.expander("Xem bảng dữ liệu chi tiết"):
        st.dataframe(
            df.sort_values(by='Ngày', ascending=False),
            use_container_width=True
        )

else:
    st.warning("Chưa có dữ liệu để hiển thị. Vui lòng kiểm tra lại Google Sheets.")