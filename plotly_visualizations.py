import os
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Output folder for plots
OUTDIR = "plots"
os.makedirs(OUTDIR, exist_ok=True)

# Read dataset
CSV_PATH = "CleanedData.csv"
df = pd.read_csv(CSV_PATH, low_memory=False)

# Clean numeric columns
# Price looks like '£14.70' — strip currency and convert
if df['Price'].dtype == object:
    df['Price'] = df['Price'].astype(str).str.replace('£', '', regex=False).str.replace(',', '', regex=False)
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

# Ensure Rating and Reviews numeric
for col in ['Rating', 'Reviews']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Basic metadata
print(f"Rows: {len(df)}, columns: {list(df.columns)}")

# 1) Price distribution (histogram)
fig1 = px.histogram(df, x='Price', nbins=40, title='Price Distribution', marginal='box')
fig1.update_layout(xaxis_title='Price (GBP)', yaxis_title='Count')
fig1.write_html(os.path.join(OUTDIR, '01_price_histogram.html'), include_plotlyjs='cdn')

# 2) Box plot: Price by top Sub Category (limit to top 10 subcategories)
if 'Sub Category' in df.columns:
    top_subs = df['Sub Category'].value_counts().nlargest(10).index.tolist()
    df_sub = df[df['Sub Category'].isin(top_subs)]
    fig2 = px.box(df_sub, x='Sub Category', y='Price', title='Price by Sub Category (top 10)')
    fig2.update_layout(xaxis_title='Sub Category', yaxis_title='Price (GBP)')
    fig2.write_html(os.path.join(OUTDIR, '02_price_by_subcategory_box.html'), include_plotlyjs='cdn')

# 3) Scatter: Price vs Rating sized by Reviews
if {'Price', 'Rating'}.issubset(df.columns):
    fig3 = px.scatter(df, x='Price', y='Rating', size='Reviews' if 'Reviews' in df.columns else None,
                      color='Main Category' if 'Main Category' in df.columns else None,
                      hover_data=['Product Name'] if 'Product Name' in df.columns else None,
                      title='Price vs Rating (size=Reviews)')
    fig3.update_layout(xaxis_title='Price (GBP)', yaxis_title='Rating')
    fig3.write_html(os.path.join(OUTDIR, '03_price_vs_rating_scatter.html'), include_plotlyjs='cdn')

# 4) Bar chart: Top products by number of reviews (top 15)
if 'Reviews' in df.columns and 'Product Name' in df.columns:
    top_reviews = df.nlargest(15, 'Reviews')[['Product Name', 'Reviews']].drop_duplicates()
    fig4 = px.bar(top_reviews[::-1], x='Reviews', y='Product Name', orientation='h',
                  title='Top 15 Products by Reviews')
    fig4.update_layout(xaxis_title='Reviews', yaxis_title='Product Name')
    fig4.write_html(os.path.join(OUTDIR, '04_top_products_by_reviews.html'), include_plotlyjs='cdn')

# 5) Correlation heatmap for numeric columns
num_cols = df.select_dtypes(include=['number']).columns.tolist()
if len(num_cols) >= 2:
    corr = df[num_cols].corr()
    fig5 = px.imshow(corr, text_auto=True, title='Numeric Feature Correlation')
    fig5.write_html(os.path.join(OUTDIR, '05_correlation_heatmap.html'), include_plotlyjs='cdn')

# 6) Treemap: Main Category -> Sub Category counts
if 'Main Category' in df.columns and 'Sub Category' in df.columns:
    fig6 = px.treemap(df, path=['Main Category', 'Sub Category'], title='Category Breakdown (treemap)')
    fig6.write_html(os.path.join(OUTDIR, '06_category_treemap.html'), include_plotlyjs='cdn')

# Optional: try to save PNG versions (requires kaleido)
SAVE_PNG = True
if SAVE_PNG:
    try:
        # small helper mapping of html filenames to png names
        html_png_pairs = [
            ('01_price_histogram.html', '01_price_histogram.png'),
            ('02_price_by_subcategory_box.html', '02_price_by_subcategory_box.png'),
            ('03_price_vs_rating_scatter.html', '03_price_vs_rating_scatter.png'),
            ('04_top_products_by_reviews.html', '04_top_products_by_reviews.png'),
            ('05_correlation_heatmap.html', '05_correlation_heatmap.png'),
            ('06_category_treemap.html', '06_category_treemap.png'),
        ]
        for h, p in html_png_pairs:
            html_path = os.path.join(OUTDIR, h)
            png_path = os.path.join(OUTDIR, p)
            if os.path.exists(html_path):
                # load figure from HTML then write image — simpler to reuse the fig objects above
                # we saved fig objects as fig1..fig6; write image if variable exists
                try:
                    # Attempt to map by name
                    varname = 'fig' + h.split('_')[0]
                    fig_obj = globals().get(varname)
                    if fig_obj is not None:
                        pio.write_image(fig_obj, png_path, format='png', scale=2)
                except Exception:
                    pass
    except Exception as e:
        print('PNG export failed (kaleido may be missing):', e)

print(f"Plots written to {OUTDIR}/ — open the HTML files in a browser.")
