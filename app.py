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

    # --- XỬ LÝ SẮP XẾP VÀ NHÓM THEO THÁNG ---
    # Tạo cột phụ để sắp xếp chính xác theo thời gian (năm trước tháng sau)
    df['Sort_Period'] = df['Ngày'].dt.to_period('M')

    # Nhóm dữ liệu và tính tổng
    df_monthly = df.groupby(['Sort_Period', 'Tháng/Năm'])['Tiền Tips'].sum().reset_index()

    # Sắp xếp lại bảng dữ liệu theo đúng trình tự thời gian
    df_monthly = df_monthly.sort_values('Sort_Period')

    st.subheader("🗓️ Tổng hợp thu nhập theo tháng")

    # Hiển thị Metrics theo hàng ngang
    cols = st.columns(len(df_monthly))
    for index, row in df_monthly.iterrows():
        with cols[index]:
            st.metric(label=f"Tháng {row['Tháng/Năm']}", value=f"{row['Tiền Tips']:,.0f} VNĐ")

    st.divider()

    # --- BIỂU ĐỒ CỘT SO SÁNH CÁC THÁNG ---
    st.subheader("📊 Biểu đồ so sánh thu nhập các tháng")
    fig_col = px.bar(
        df_monthly,
        x='Tháng/Năm',
        y='Tiền Tips',
        text_auto=',.0f',  # Hiển thị con số trên đầu cột
        title="Tổng tiền Tips nhận được theo từng tháng",
        color='Tiền Tips',  # Màu sắc thay đổi theo độ cao của cột
        color_continuous_scale='Viridis'
    )

    # Đảm bảo trục X không bị tự động sắp xếp lại theo chữ cái
    fig_col.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_monthly['Tháng/Năm']})

    st.plotly_chart(fig_col, use_container_width=True)

    # --- BẢNG CHI TIẾT ---
    with st.expander("Xem bảng dữ liệu chi tiết hàng ngày"):
        st.dataframe(df.sort_values(by='Ngày', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")