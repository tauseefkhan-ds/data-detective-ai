
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Data Detective AI",
    page_icon="🔎",
    layout="wide"
)

st.title("Data Detective AI")
st.write("Investigate your business data and discover data quality issues.")

uploaded_file = st.file_uploader("Upload your business CSV", type=["csv"])

if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file)
        st.success("CSV uploaded successfully!")

        # Basic metrics without Streamlit metric components
        a, b, c = st.columns(3)
        a.write("TOTAL ROWS")
        a.title(str(data.shape[0]))
        b.write("TOTAL COLUMNS")
        b.title(str(data.shape[1]))
        c.write("MISSING VALUES")
        c.title(str(int(data.isnull().sum().sum())))

        st.subheader("Data Preview")
        st.markdown(data.head(20).to_html(index=False), unsafe_allow_html=True)

        st.subheader("Missing Values Report")
        missing = data.isnull().sum()
        missing_report = missing[missing > 0]

        if missing_report.empty:
            st.success("No missing values found.")
        else:
            st.markdown(
                missing_report.rename("Missing Count").to_frame().to_html(),
                unsafe_allow_html=True
            )

        st.subheader("Duplicate Records")
        st.write(f"Exact duplicate rows: {int(data.duplicated().sum())}")

        st.subheader("Numeric Summary")
        numeric = data.select_dtypes(include="number")

        if not numeric.empty:
            st.markdown(
                numeric.describe().round(2).to_html(),
                unsafe_allow_html=True
            )
        else:
            st.info("No numeric columns found.")

        st.download_button(
            "Download CSV",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name="business_data_export.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Could not read this CSV: {e}")
else:
    st.info("Upload a CSV file to start.")
