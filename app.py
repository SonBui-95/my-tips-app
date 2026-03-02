import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="My Tips Dashboard", layout="wide")
st.title("📊 Báo Cáo Tiền Tips Theo Tháng")


# --- KẾT NỐI DỮ LIỆU ---
@st.cache_data(ttl=600)
def load_data():
    # 1. Khai báo scope rõ ràng ở đầu hàm
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    try:
        # 2. Lấy credentials từ Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 3. Mở sheet (Lưu ý: Tên file "tips_received" phải khớp 100%)
        sheet = client.open("tips_received").sheet1
        data = sheet.get_all_records()

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 4. Xử lý định dạng ngày tháng an toàn
        if 'Ngày' in df.columns:
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True, errors='coerce')
            # Loại bỏ các dòng bị lỗi ngày (NaT)
            df = df.dropna(subset=['Ngày'])
            df['Tháng/Năm'] = df['Ngày'].dt.strftime('%m/%Y')
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()


# --- HIỂN THỊ ---
try:
    df = load_data()

    if not df.empty:
        # Tạo cột phụ sắp xếp
        df['Sort_Period'] = df['Ngày'].dt.to_period('M')

        # Nhóm dữ liệu
        df_monthly = df.groupby(['Sort_Period', 'Tháng/Năm'])['Tiền Tips'].sum().reset_index()
        df_monthly = df_monthly.sort_values('Sort_Period')

        st.subheader("🗓️ Tổng hợp thu nhập theo tháng")

        # Hiển thị Metrics (Chỉ hiển thị nếu có dữ liệu tháng)
        if len(df_monthly) > 0:
            cols = st.columns(len(df_monthly))
            for index, row in df_monthly.iterrows():
                with cols[index]:
                    st.metric(label=f"Tháng {row['Tháng/Năm']}", value=f"{row['Tiền Tips']:,.0f} VNĐ")

        st.divider()

        # --- BIỂU ĐỒ CỘT ---
        st.subheader("📊 Biểu đồ so sánh thu nhập các tháng")
        fig_col = px.bar(
            df_monthly,
            x='Tháng/Năm',
            y='Tiền Tips',
            text_auto=',.0f',
            color='Tiền Tips',
            color_continuous_scale='Viridis'
        )
        fig_col.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_monthly['Tháng/Năm'].tolist()})
        st.plotly_chart(fig_col, use_container_width=True)

        # --- BẢNG CHI TIẾT ---
        with st.expander("Xem bảng dữ liệu chi tiết hàng ngày"):
            st.dataframe(df.sort_values(by='Ngày', ascending=False), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu nào trong Google Sheets để hiển thị.")

except Exception as e:
    st.error(f"Đã xảy ra lỗi khi xử lý biểu đồ: {e}")