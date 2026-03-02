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
    # 1. Định nghĩa scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # 2. Lấy thông tin từ Secrets (Phải khớp với tên trong Streamlit Cloud Secrets)
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 3. Mở file (Tên file phải chính xác 100% như trên Google Sheets)
        sheet = client.open("tips_received").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        # 4. Xử lý dữ liệu
        if not df.empty and 'Ngày' in df.columns:
            # Chuyển cột Ngày sang định dạng datetime
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True)
            # Tạo cột Tháng/Năm để nhóm dữ liệu
            df['Tháng/Năm'] = df['Ngày'].dt.strftime('%m/%Y')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi kết nối hoặc dữ liệu: {e}")
        return pd.DataFrame()


# --- HIỂN THỊ GIAO DIỆN ---
try:
    df = load_data()

    if not df.empty:
        # --- XỬ LÝ SẮP XẾP VÀ NHÓM THEO THÁNG ---
        # Tạo cột phụ để sắp xếp thời gian chuẩn
        df['Sort_Period'] = df['Ngày'].dt.to_period('M')

        # Tính tổng tiền tips theo tháng
        df_monthly = df.groupby(['Sort_Period', 'Tháng/Năm'])['Tiền Tips'].sum().reset_index()
        df_monthly = df_monthly.sort_values('Sort_Period')

        st.subheader("🗓️ Tổng hợp thu nhập theo tháng")

        # Hiển thị số tổng dưới dạng thẻ (Metrics)
        cols = st.columns(len(df_monthly))
        for index, row in df_monthly.iterrows():
            with cols[index]:
                st.metric(label=f"Tháng {row['Tháng/Năm']}", value=f"{row['Tiền Tips']:,.0f} VNĐ")

        st.divider()

        # --- BIỂU ĐỒ CỘT ---
        st.subheader("📊 Biểu đồ so sánh thu nhập")
        fig_col = px.bar(
            df_monthly,
            x='Tháng/Năm',
            y='Tiền Tips',
            text_auto=',.0f',
            title="Tổng tiền Tips nhận được",
            color='Tiền Tips',
            color_continuous_scale='Viridis'
        )
        # Giữ đúng thứ tự tháng trên trục X
        fig_col.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_monthly['Tháng/Năm']})
        st.plotly_chart(fig_col, use_container_width=True)

        # --- BẢNG CHI TIẾT ---
        with st.expander("Xem chi tiết lịch sử nhận tips"):
            st.dataframe(df.sort_values(by='Ngày', ascending=False), use_container_width=True)

    else:
        st.warning("Đang chờ dữ liệu từ Google Sheets... Hãy đảm bảo bạn đã nhập dữ liệu vào file.")

except Exception as e:
    st.error(f"Đã xảy ra lỗi hiển thị: {e}")