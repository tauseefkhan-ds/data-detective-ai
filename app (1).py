
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Data Detective AI",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Data Detective AI")
st.write("Investigate your business data and discover data quality issues.")

uploaded_file = st.file_uploader(
    "Upload your business CSV",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file)
        st.success("CSV uploaded successfully!")

        # Basic metrics
        a, b, c = st.columns(3)

        a.write("TOTAL ROWS")
        a.title(str(data.shape[0]))

        b.write("TOTAL COLUMNS")
        b.title(str(data.shape[1]))

        c.write("MISSING VALUES")
        c.title(str(int(data.isnull().sum().sum())))

        # Data preview
        st.subheader("📋 Data Preview")
        st.dataframe(data.head(20), use_container_width=True)

        # Missing values
        st.subheader("🔍 Missing Values Report")
        missing = data.isnull().sum()
        missing_report = missing[missing > 0]

        if missing_report.empty:
            st.success("No missing values found.")
        else:
            st.dataframe(
                missing_report.rename("Missing Count").to_frame()
            )

        # Exact duplicate rows
        st.subheader("📑 Duplicate Records")
        duplicate_rows = int(data.duplicated().sum())
        st.write(f"Exact duplicate rows: {duplicate_rows}")

        if duplicate_rows > 0:
            st.warning("Duplicate rows were detected.")
        else:
            st.success("No exact duplicate rows found.")

        # Duplicate Order IDs
        st.subheader("🆔 Duplicate Order IDs")

        if "Order_ID" in data.columns:
            duplicate_ids = data[
                data["Order_ID"].notna()
                & data["Order_ID"].duplicated(keep=False)
            ]

            st.write(f"Rows with repeated Order IDs: {len(duplicate_ids)}")

            if not duplicate_ids.empty:
                st.warning("Repeated Order IDs found.")
                st.dataframe(duplicate_ids, use_container_width=True)
            else:
                st.success("No repeated Order IDs found.")
        else:
            st.info("No 'Order_ID' column found in this CSV.")

        # Negative profit detection
        st.subheader("💰 Negative Profit Detection")

        if "Profit" in data.columns:
            profit = pd.to_numeric(data["Profit"], errors="coerce")
            loss_rows = data[profit < 0]

            st.write(f"Orders with negative profit: {len(loss_rows)}")

            if not loss_rows.empty:
                st.warning("Loss-making orders detected.")
                st.dataframe(loss_rows, use_container_width=True)
            else:
                st.success("No negative profit found.")
        else:
            st.info("No 'Profit' column found in this CSV.")

        # Numeric summary
        st.subheader("📊 Numeric Summary")
        numeric = data.select_dtypes(include="number")

        if not numeric.empty:
            st.dataframe(numeric.describe().round(2))
        else:
            st.info("No numeric columns found.")

        # Download original data
        st.download_button(
            "⬇️ Download CSV",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name="business_data_export.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Could not read this CSV: {e}")

else:
    st.info("Upload a CSV file to start.")
