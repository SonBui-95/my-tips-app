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
    # 1. Định nghĩa scope TRƯỚC khi sử dụng
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # 2. Lấy dictionary từ Secrets (Đảm bảo bạn đã lưu Secrets thành công trên Streamlit Cloud)
    creds_dict = st.secrets["gcp_service_account"]

    # 3. Kết nối Google Sheets
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 4. Mở file và lấy dữ liệu
        sheet = client.open("tips_received").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        # 5. Xử lý định dạng ngày tháng
        if 'Ngày' in df.columns:
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True)
            df['Tháng/Năm'] = df['Ngày'].dt.strftime('%m/%Y')
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()


try:
    df = load_data()

    if not df.empty:
        # --- XỬ LÝ SẮP XẾP VÀ NHÓM THEO THÁNG ---
        df['Sort_Period'] = df['Ngày'].dt.to_period('M')
        df_monthly = df.groupby(['Sort_Period', 'Tháng/Năm'])['Tiền Tips'].sum().reset_index()
        df_monthly = df_monthly.sort_values('Sort_Period')

        st.subheader("🗓️ Tổng hợp thu nhập theo tháng")
        cols = st.columns(len(df_monthly))
        for index, row in df_monthly.iterrows():
            with cols[index]:
                st.metric(label=f"Tháng {row['Tháng/Năm']}", value=f"{row['Tiền Tips']:,.0f} VNĐ")

        st.divider()

        # --- BIỂU ĐỒ CỘT ---
        st.subheader("📊 Biểu đồ so sánh thu nhập các tháng")
        fig_col = px.bar(
            df_monthly, x='Tháng/Năm', y='Tiền Tips',
            text_auto=',.0f', title="Tổng tiền Tips theo tháng",
            color='Tiền Tips', color_continuous_scale='Viridis'
        )
        fig_col.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_monthly['Tháng/Năm']})
        st.plotly_chart(fig_col, use_container_width=True)

        with st.expander("Xem bảng dữ liệu chi tiết"):
            st.dataframe(df.sort_values(by='Ngày', ascending=False), use_container_width=True)
    else:
        st.warning("Chưa có dữ liệu để hiển thị. Vui lòng kiểm tra lại Google Sheets.")

except Exception as e:
    st.error(f"Lỗi hiển thị: {e}")