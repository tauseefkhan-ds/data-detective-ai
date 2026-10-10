
import streamlit as st
import pandas as pd
from groq import Groq
from io import StringIO

st.set_page_config(
    page_title="Data Detective AI",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Data Detective AI")
st.write(
    "Investigate your business data and discover "
    "data quality issues with AI-powered insights."
)

# ---------- API CONFIGURATION ----------

def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )
    return Groq(api_key=api_key)


# ---------- CSV UPLOAD ----------

uploaded_file = st.file_uploader(
    "Upload your business CSV",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file)

        if data.empty:
            st.warning("The uploaded CSV has no data rows.")
            st.stop()

        if len(data.columns) == 0:
            st.warning("No columns were found in this CSV.")
            st.stop()

        st.success("CSV uploaded successfully!")

        # ---------- CLEAN COLUMN NAMES ----------

        data.columns = data.columns.astype(str).str.strip()

        st.subheader("📌 Data Overview")

        total_rows = len(data)
        total_columns = len(data.columns)
        missing_count = int(data.isna().sum().sum())

        col1, col2, col3 = st.columns(3)

        col1.metric("TOTAL ROWS", f"{total_rows:,}")
        col2.metric("TOTAL COLUMNS", f"{total_columns:,}")
        col3.metric("MISSING VALUES", f"{missing_count:,}")

        # ---------- DATA PREPARATION ----------

        numeric_data = data.select_dtypes(include="number")

        sales_col = next(
            (c for c in data.columns
             if c.lower() == "sales"),
            None
        )
        profit_col = next(
            (c for c in data.columns
             if c.lower() == "profit"),
            None
        )
        product_col = next(
            (c for c in data.columns
             if c.lower() == "product"),
            None
        )
        region_col = next(
            (c for c in data.columns
             if c.lower() == "region"),
            None
        )
        order_id_col = next(
            (c for c in data.columns
             if c.lower() == "order_id"),
            None
        )

        sales = (
            pd.to_numeric(data[sales_col], errors="coerce")
            if sales_col else None
        )
        profit = (
            pd.to_numeric(data[profit_col], errors="coerce")
            if profit_col else None
        )

        # ---------- BUSINESS PERFORMANCE ----------

        st.subheader("💼 Business Performance Overview")

        if sales is not None and profit is not None:
            total_sales = sales.sum()
            total_profit = profit.sum()

            profit_margin = (
                (total_profit / total_sales) * 100
                if total_sales != 0 else 0
            )

            loss_orders = int((profit < 0).sum())

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("TOTAL SALES", f"{total_sales:,.2f}")
            col2.metric("TOTAL PROFIT", f"{total_profit:,.2f}")
            col3.metric("PROFIT MARGIN", f"{profit_margin:.2f}%")
            col4.metric("LOSS ORDERS", f"{loss_orders:,}")
        else:
            st.info(
                "Business metrics require numeric Sales and Profit columns."
            )
            total_sales = None
            total_profit = None
            profit_margin = None
            loss_orders = None

        # ---------- DATA PREVIEW ----------

        st.subheader("📋 Data Preview")
        st.dataframe(data.head(20), use_container_width=True)

        # ---------- MISSING VALUES ----------

        st.subheader("🔍 Missing Values Report")

        missing_report = data.isna().sum()
        missing_report = missing_report[missing_report > 0]

        if missing_report.empty:
            st.success("No missing values found.")
        else:
            st.dataframe(
                missing_report.rename("Missing Count").to_frame(),
                use_container_width=True
            )

        # ---------- DUPLICATE ROWS ----------

        st.subheader("📑 Duplicate Records")

        duplicate_mask = data.duplicated(keep=False)
        duplicate_count = int(data.duplicated().sum())

        st.write(f"Exact duplicate rows: {duplicate_count}")

        if duplicate_count > 0:
            st.warning("Duplicate rows were detected.")
            st.dataframe(
                data[duplicate_mask],
                use_container_width=True
            )
        else:
            st.success("No exact duplicate rows found.")

        # ---------- REPEATED ORDER IDS ----------

        st.subheader("🆔 Duplicate Order IDs")

        repeated_id_count = 0

        if order_id_col:
            valid_ids = data[order_id_col].notna()
            repeated_mask = (
                valid_ids
                & data[order_id_col].duplicated(keep=False)
            )

            repeated_id_count = int(
                data.loc[repeated_mask, order_id_col].nunique()
            )

            repeated_rows = int(repeated_mask.sum())

            st.write(
                f"Rows with repeated Order IDs: {repeated_rows}"
            )

            if repeated_rows > 0:
                st.warning("Repeated Order IDs found.")
                st.dataframe(
                    data.loc[repeated_mask],
                    use_container_width=True
                )
            else:
                st.success("No repeated Order IDs found.")
        else:
            st.info("No Order_ID column found in this dataset.")

        # ---------- NEGATIVE PROFIT ----------

        st.subheader("💰 Negative Profit Detection")

        if profit is not None:
            negative_mask = profit < 0
            negative_count = int(negative_mask.sum())

            st.write(
                f"Orders with negative profit: {negative_count}"
            )

            if negative_count > 0:
                st.warning("Loss-making orders detected.")
                st.dataframe(
                    data.loc[negative_mask],
                    use_container_width=True
                )
            else:
                st.success("No negative-profit orders found.")
        else:
            st.info("No numeric Profit column found.")

        # ---------- SALES AND PROFIT CHARTS ----------

        st.subheader("📈 Sales and Profit Analysis")

        if product_col and sales is not None:
            sales_by_product = (
                pd.DataFrame({
                    "Product": data[product_col],
                    "Sales": sales
                })
                .groupby("Product", dropna=False)["Sales"]
                .sum()
                .sort_values(ascending=False)
            )

            st.write("**Sales by Product**")
            st.bar_chart(sales_by_product)

        if product_col and profit is not None:
            profit_by_product = (
                pd.DataFrame({
                    "Product": data[product_col],
                    "Profit": profit
                })
                .groupby("Product", dropna=False)["Profit"]
                .sum()
                .sort_values(ascending=False)
            )

            st.write("**Profit by Product**")
            st.bar_chart(profit_by_product)

        # ---------- BUSINESS RECOMMENDATIONS ----------

        st.subheader("💡 Business Recommendations")

        recommendations = []

        if duplicate_count > 0:
            recommendations.append(
                "Review exact duplicate rows before calculating final KPIs."
            )

        if repeated_id_count > 0:
            recommendations.append(
                "Check repeated Order IDs to determine whether "
                "they represent duplicate orders or valid records."
            )

        if profit is not None and (profit < 0).any():
            recommendations.append(
                "Investigate loss-making orders and review their "
                "costs, selling prices, and discounts."
            )

        if sales is not None and profit is not None:
            recommendations.append(
                "Compare sales and profit together; high sales "
                "do not always mean high profitability."
            )

        if product_col and sales is not None:
            best_product = sales_by_product.idxmax()
            recommendations.append(
                f"Review the sales performance of {best_product}, "
                "which has the highest total sales in this dataset."
            )

        if missing_count > 0:
            recommendations.append(
                "Resolve missing values where they affect analysis."
            )

        if not recommendations:
            recommendations.append(
                "Continue monitoring data quality and business performance."
            )

        for i, recommendation in enumerate(recommendations, 1):
            st.write(f"{i}. {recommendation}")

        # ---------- AI BUSINESS INSIGHTS ----------

        st.subheader("🤖 AI Business Insights")

        if st.button("Generate AI Insights", type="primary"):
            try:
                client = get_groq_client()

                # Create a compact dataset summary for the AI.
                summary_parts = [
                    f"Rows: {len(data)}",
                    f"Columns: {', '.join(data.columns)}",
                    f"Missing cells: {missing_count}",
                    f"Exact duplicate rows: {duplicate_count}",
                    f"Rows with repeated Order IDs: "
                    f"{int((data[order_id_col].notna() & data[order_id_col].duplicated(keep=False)).sum()) if order_id_col else 0}"
                ]

                if sales is not None and profit is not None:
                    summary_parts.extend([
                        f"Total sales: {sales.sum():.2f}",
                        f"Total profit: {profit.sum():.2f}",
                        f"Overall profit margin: "
                        f"{(profit.sum() / sales.sum() * 100) if sales.sum() else 0:.2f}%",
                        f"Orders with negative profit: {int((profit < 0).sum())}"
                    ])

                # Limit sample data to keep the prompt manageable.
                sample_csv = data.head(30).to_csv(index=False)

                numeric_summary = (
                    numeric_data.describe()
                    .round(2)
                    .to_string()
                    if not numeric_data.empty
                    else "No numeric columns available."
                )

                prompt = f"""
You are a careful business data analyst.

Analyze the dataset summary below and write a useful business report.

DATASET SUMMARY:
{chr(10).join(summary_parts)}

NUMERIC SUMMARY:
{numeric_summary}

SAMPLE DATA (up to 30 rows):
{sample_csv}

STRICT OUTPUT RULES:
- Use plain Markdown with simple headings and bullet points.
- Do NOT use Markdown tables.
- Do NOT use HTML, LaTeX, or decorative formatting.
- Write numbers normally, such as 1,400 to 78,000.
- Do not repeat or merge words.
- Use these exact sections:
  1. Key Observations
  2. Data Quality Issues
  3. Business Performance Insights
  4. Practical Recommendations
  5. Limitations
- Keep the report under 700 words.
- Finish every section and every sentence.
- Do not invent statistics that cannot be verified from the supplied data.
- Clearly distinguish observed facts from possible explanations.
- Do not claim that duplicate records have been removed.
- If data is limited, explain that conclusions are preliminary.
- If a field is absent, state that it is unavailable.
- Return only the report, with no introduction about your own process.
"""

                with st.spinner("AI is analyzing your business data..."):
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You produce concise, accurate business "
                                    "analysis in clean Markdown. Follow the "
                                    "requested structure and finish the report."
                                )
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.1,
                        max_tokens=3000
                    )

                ai_report = response.choices[0].message.content

                if not ai_report or not ai_report.strip():
                    st.error("The AI returned an empty report.")
                else:
                    st.markdown(ai_report)

                    st.download_button(
                        label="📥 Download AI Insights Report",
                        data=ai_report,
                        file_name="AI_Business_Insights.md",
                        mime="text/markdown"
                    )

            except Exception as e:
                st.error(
                    f"AI Error: {type(e).__name__}: {e}"
                )

        # ---------- DOWNLOAD ANALYSIS REPORT ----------

        st.subheader("📄 Download Analysis Report")

        report_lines = [
            "DATA DETECTIVE AI - ANALYSIS REPORT",
            "=" * 40,
            f"Rows: {total_rows}",
            f"Columns: {total_columns}",
            f"Missing cells: {missing_count}",
            f"Exact duplicate rows: {duplicate_count}",
            f"Rows with repeated Order IDs: "
            f"{int((data[order_id_col].notna() & data[order_id_col].duplicated(keep=False)).sum()) if order_id_col else 0}",
            f"Orders with negative profit: "
            f"{int((profit < 0).sum()) if profit is not None else 'N/A'}",
            "",
            "MISSING VALUES BY COLUMN",
            missing_report.to_string() if not missing_report.empty
            else "No missing values found.",
            "",
            "NUMERIC SUMMARY",
            numeric_data.describe().round(2).to_string()
            if not numeric_data.empty else "No numeric data."
        ]

        if sales is not None and profit is not None:
            report_lines.extend([
                "",
                "BUSINESS PERFORMANCE",
                f"Total sales: {sales.sum():,.2f}",
                f"Total profit: {profit.sum():,.2f}",
                f"Overall profit margin: "
                f"{(profit.sum() / sales.sum() * 100) if sales.sum() else 0:.2f}%",
                f"Loss orders: {int((profit < 0).sum())}"
            ])

        report_text = "\n".join(report_lines)

        st.download_button(
            label="📄 Download Analysis Report",
            data=report_text,
            file_name="Data_Detective_Analysis.txt",
            mime="text/plain"
        )

        # ---------- DOWNLOAD DATA ----------

        st.download_button(
            label="📥 Download Original CSV",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name="analyzed_business_data.csv",
            mime="text/csv"
        )

        # ---------- NUMERIC SUMMARY ----------

        st.subheader("📊 Numeric Summary")

        if not numeric_data.empty:
            st.dataframe(
                numeric_data.describe().round(2),
                use_container_width=True
            )
        else:
            st.info("No numeric columns are available for summary.")

    except Exception as e:
        st.error(
            f"Could not process this CSV: {type(e).__name__}: {e}"
        )

else:
    st.info("Upload a CSV file to begin your analysis.")
