import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="解剖学 穴埋めアプリ", layout="centered")

# 1. データの読み込み
@st.cache_data
def load_data():
    try:
        # NA（空欄）を空文字列として読み込むことでエラーを防ぐ
        return pd.read_csv("anatomy_data.csv", keep_default_na=False)
    except FileNotFoundError:
        st.error("同じフォルダに anatomy_data.csv が見つかりません。")
        st.stop()

df = load_data()

# 2. サイドバーの設定（章の複数選択と出題順）
st.sidebar.title("設定")
chapters = df['章'].unique()
selected_chapters = st.sidebar.multiselect(
    "学習する章を選択してください（複数選択可）", 
    chapters, 
    default=chapters[0]
)

if not selected_chapters:
    st.warning("👈 サイドバーから学習する章を1つ以上選んでください。")
    st.stop()

order_mode = st.sidebar.radio("出題順", ["順番", "ランダム"])

# 3. セッション状態の初期化
if ('current_chapters' not in st.session_state or 
    st.session_state.current_chapters != selected_chapters or
    st.session_state.get('order_mode') != order_mode):
    
    st.session_state.current_chapters = selected_chapters
    st.session_state.order_mode = order_mode
    st.session_state.index = 0
    st.session_state.score_ja = 0
    st.session_state.score_la = 0
    st.session_state.total_blanks = 0
    st.session_state.history = []
    st.session_state.answered = False
    
    # 選択された章を抽出し、ランダムならシャッフルする
    temp_df = df[df['章'].isin(selected_chapters)]
    if order_mode == "ランダム":
        temp_df = temp_df.sample(frac=1)
        
    st.session_state.chapter_df = temp_df.reset_index(drop=True)

chapter_df = st.session_state.chapter_df

# 4. 全問終了時のリザルト＆復習リスト画面
if st.session_state.index >= len(chapter_df):
    selected_names = ", ".join(selected_chapters)
    st.title(f"🎉 {selected_names} 完了！")
    
    st.write("### 最終スコア")
    st.write(f"- **日本語:** {st.session_state.score_ja} / {st.session_state.total_blanks} 正解")
    st.write(f"- **ラテン語:** {st.session_state.score_la} / {st.session_state.total_blanks} 正解")
    
    st.write("---")
    st.write("### 📝 復習リスト")
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            with st.expander(f"問題 {i+1}", expanded=True):
                st.write(f"**問題:** {item['問題']}")
                
                # 詳細データをデータフレーム化して美しい表(テーブル)として表示
                df_detail = pd.DataFrame(item['詳細']).set_index("空欄")
                st.table(df_detail)
    
    if st.button("もう一度解く", type="primary"):
        st.session_state.index = 0
        st.session_state.score_ja = 0
        st.session_state.score_la = 0
        st.session_state.total_blanks = 0
        st.session_state.history = []
        st.session_state.answered = False
        
        # もう一度解く際、ランダムモードなら再シャッフルする
        if st.session_state.order_mode == "ランダム":
            st.session_state.chapter_df = df[df['章'].isin(st.session_state.current_chapters)].sample(frac=1).reset_index(drop=True)
            
        st.rerun()
    st.stop()

# 5. 現在の問題の表示
current_q = chapter_df.iloc[st.session_state.index]

st.title("解剖学 穴埋めテスト")
st.progress(st.session_state.index / len(chapter_df))
st.write(f"**問題 {st.session_state.index + 1} / {len(chapter_df)}** ({current_q['章']})")
st.info(current_q['問題文'])

# 6. 入力フォームの生成
user_inputs = {}
blanks_count = 0

with st.form(key=f"question_form_{st.session_state.index}"):
    for i in range(1, 4):
        ja_col = f"日本語{i}"
        la_col = f"ラテン語{i}"
        
        if current_q.get(ja_col) != "":
            blanks_count += 1
            st.markdown(f"**【空欄 {i}】**")
            col1, col2 = st.columns(2)
            with col1:
                # autocomplete="off" と、keyへの問題番号の付与でリセット機能を確実にする
                user_inputs[f"ja_{i}"] = st.text_input("日本語:", key=f"ja_{st.session_state.index}_{i}", autocomplete="off")
            with col2:
                # autocomplete="off" と、keyへの問題番号の付与でリセット機能を確実にする
                user_inputs[f"la_{i}"] = st.text_input("ラテン語:", key=f"la_{st.session_state.index}_{i}", autocomplete="off")
            st.divider()
            
    submit_btn = st.form_submit_button("採点する")

# 7. 採点と記録処理
if submit_btn and not st.session_state.answered:
    st.session_state.answered = True
    
    details = []  # 表を作るためのリスト
    
    for i in range(1, blanks_count + 1):
        correct_ja = str(current_q[f"日本語{i}"]).strip()
        correct_la = str(current_q[f"ラテン語{i}"]).strip()
        
        user_ja = user_inputs[f"ja_{i}"].strip()
        user_la = user_inputs[f"la_{i}"].strip()
        
        st.markdown(f"#### 【空欄 {i} の結果】")
        
        if user_ja == correct_ja:
            st.success(f"✅ 日本語: 正解！")
            st.session_state.score_ja += 1
            res_ja = f"✅ {correct_ja}"
        else:
            st.error(f"❌ 日本語: 不正解 (回答: {user_ja} ➔ **正解: {correct_ja}**)")
            res_ja = f"❌ {correct_ja}"
            
        if user_la == correct_la:
            st.success(f"✅ ラテン語: 正解！")
            st.session_state.score_la += 1
            res_la = f"✅ {correct_la}"
        else:
            st.error(f"❌ ラテン語: 不正解 (回答: {user_la} ➔ **正解: {correct_la}**)")
            res_la = f"❌ {correct_la}"
            
        st.session_state.total_blanks += 1
        
        # 空欄ごとの結果をまとめてリストに追加
        details.append({
            "空欄": f"[{i}]",
            "日本語": res_ja,
            "ラテン語": res_la
        })

    record = {
        "問題": current_q['問題文'],
        "詳細": details
    }
    st.session_state.history.append(record)
    st.session_state.show_next = True

# 8. 次の問題へ進むボタン
if st.session_state.get('show_next', False):
    if st.button("次の問題へ", type="primary"):
        st.session_state.index += 1
        st.session_state.answered = False
        st.session_state.show_next = False
        st.rerun()