import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="解剖学 穴埋めアプリ", layout="centered")

# ==========================================
# 1. データの読み込み
# ==========================================
@st.cache_data
def load_data():
    try:
        # NA（空欄）を空文字列として読み込むことでエラーを防ぐ
        return pd.read_csv("anatomy_data.csv", keep_default_na=False)
    except FileNotFoundError:
        st.error("同じフォルダに anatomy_data.csv が見つかりません。")
        st.stop()

df = load_data()

# ==========================================
# 2. サイドバーの設定（章の複数選択と出題順）
# ==========================================
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

# ==========================================
# 3. セッション状態（記憶）の初期化
# ==========================================
if ('current_chapters' not in st.session_state or 
    st.session_state.current_chapters != selected_chapters or
    st.session_state.get('order_mode') != order_mode):
    
    st.session_state.current_chapters = selected_chapters
    st.session_state.order_mode = order_mode
    st.session_state.index = 0
    st.session_state.score_ja = 0
    st.session_state.score_la = 0
    st.session_state.total_ja_blanks = 0
    st.session_state.total_la_blanks = 0
    st.session_state.history = []
    
    # 画面切り替え用のフラグ
    st.session_state.answered = False
    st.session_state.scored_this_turn = False
    st.session_state.temp_inputs = {}
    
    # 選択された章を抽出し、ランダムならシャッフルする
    temp_df = df[df['章'].isin(selected_chapters)]
    if order_mode == "ランダム":
        temp_df = temp_df.sample(frac=1)
        
    st.session_state.chapter_df = temp_df.reset_index(drop=True)

chapter_df = st.session_state.chapter_df

# ==========================================
# 4. 全問終了時のリザルト＆復習リスト画面
# ==========================================
if st.session_state.index >= len(chapter_df):
    selected_names = ", ".join(selected_chapters)
    st.title(f"🎉 {selected_names} 完了！")
    
    st.write("### 最終スコア")
    st.write(f"- **日本語:** {st.session_state.score_ja} / {st.session_state.total_ja_blanks} 正解")
    st.write(f"- **ラテン語:** {st.session_state.score_la} / {st.session_state.total_la_blanks} 正解")
    
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
        st.session_state.total_ja_blanks = 0
        st.session_state.total_la_blanks = 0
        st.session_state.history = []
        st.session_state.answered = False
        st.session_state.scored_this_turn = False
        st.session_state.temp_inputs = {}
        
        # もう一度解く際、ランダムモードなら再シャッフルする
        if st.session_state.order_mode == "ランダム":
            st.session_state.chapter_df = df[df['章'].isin(st.session_state.current_chapters)].sample(frac=1).reset_index(drop=True)
            
        st.rerun()
    st.stop()

# ==========================================
# 5. 現在の問題の表示
# ==========================================
current_q = chapter_df.iloc[st.session_state.index]

st.title("解剖学 穴埋めテスト")
st.progress(st.session_state.index / len(chapter_df))
st.write(f"**問題 {st.session_state.index + 1} / {len(chapter_df)}** ({current_q['章']})")
st.info(current_q['問題文'])

user_inputs = {}

# ==========================================
# 6. 【未採点時】入力フォームの表示
# ==========================================
if not st.session_state.answered:
    with st.form(key=f"question_form_{st.session_state.index}"):

        with st.container(height=250):
            for i in range(1, 7):
                ja_col = f"日本語{i}"
                la_col = f"ラテン語{i}"
                
                ja_val = current_q.get(ja_col, "")
                la_val = current_q.get(la_col, "")
                
                # 日本語かラテン語、どちらか一方でもデータが存在するかチェック
                has_ja = pd.notna(ja_val) and str(ja_val).strip() != ""
                has_la = pd.notna(la_val) and str(la_val).strip() != ""
                
                if has_ja or has_la:
                    st.markdown(f"**【空欄 {i}】**")
                    
                    # 両方ある場合は2列
                    if has_ja and has_la:
                        col1, col2 = st.columns(2)
                        with col1:
                            user_inputs[f"ja_{i}"] = st.text_input("日本語:", key=f"ja_{st.session_state.index}_{i}", autocomplete="off")
                        with col2:
                            user_inputs[f"la_{i}"] = st.text_input("ラテン語:", key=f"la_{st.session_state.index}_{i}", autocomplete="off")
                    
                    # 日本語だけの場合は1列
                    elif has_ja:
                        user_inputs[f"ja_{i}"] = st.text_input("日本語:", key=f"ja_{st.session_state.index}_{i}", autocomplete="off")
                        user_inputs[f"la_{i}"] = ""  # エラー防止用
                    
                    # ラテン語だけの場合は1列
                    elif has_la:
                        user_inputs[f"ja_{i}"] = ""  # エラー防止用
                        user_inputs[f"la_{i}"] = st.text_input("ラテン語:", key=f"la_{st.session_state.index}_{i}", autocomplete="off")
                        
                    st.divider()
                
        # ボタンを押すと画面全体がリロード(rerun)され、下の「採点済み」ブロックへ移行する
        submit_btn = st.form_submit_button("採点する", type="primary")
        if submit_btn:
            st.session_state.answered = True
            st.session_state.temp_inputs = user_inputs  # ユーザーの入力を記憶
            st.rerun()

# ==========================================
# 7. 【採点済み】結果の表示と次の問題へ
# ==========================================
else:
    details = []
    saved_inputs = st.session_state.get('temp_inputs', {})
    
    st.write("### 📝 採点結果")
    
    with st.container(height=250):
        for i in range(1, 7):
            ja_col = f"日本語{i}"
            la_col = f"ラテン語{i}"
            
            ja_val = current_q.get(ja_col, "")
            la_val = current_q.get(la_col, "")
            
            has_ja = pd.notna(ja_val) and str(ja_val).strip() != ""
            has_la = pd.notna(la_val) and str(la_val).strip() != ""
            
            if has_ja or has_la:
                st.markdown(f"#### 【空欄 {i}】")
                
                # --- 日本語の採点 ---
                if has_ja:
                    correct_ja = str(ja_val).strip()
                    user_ja = saved_inputs.get(f"ja_{i}", "").strip()
                    
                    if user_ja == correct_ja:
                        st.success(f"✅ 日本語: 正解！ 【 {correct_ja} 】")
                        # ページリロードによるスコアの二重加算を防ぐ
                        if not st.session_state.get('scored_this_turn', False):
                            st.session_state.score_ja += 1
                        res_ja = f"✅ {correct_ja}"
                    else:
                        st.error(f"❌ 日本語: 不正解 (回答: {user_ja} ➔ **正解: {correct_ja}**)")
                        res_ja = f"❌ {correct_ja}"
                    
                    if not st.session_state.get('scored_this_turn', False):
                        st.session_state.total_ja_blanks += 1
                else:
                    res_ja = "ー (なし)"

                # --- ラテン語の採点 ---
                if has_la:
                    correct_la = str(la_val).strip()
                    user_la = saved_inputs.get(f"la_{i}", "").strip()
                    
                    if user_la == correct_la:
                        st.success(f"✅ ラテン語: 正解！ 【 {correct_la} 】")
                        if not st.session_state.get('scored_this_turn', False):
                            st.session_state.score_la += 1
                        res_la = f"✅ {correct_la}"
                    else:
                        st.error(f"❌ ラテン語: 不正解 (回答: {user_la} ➔ **正解: {correct_la}**)")
                        res_la = f"❌ {correct_la}"
                    
                    if not st.session_state.get('scored_this_turn', False):
                        st.session_state.total_la_blanks += 1
                else:
                    res_la = "ー (なし)"
                
                # 復習リスト用のデータを追加
                details.append({
                    "空欄": f"[{i}]",
                    "日本語": res_ja,
                    "ラテン語": res_la
                })
                st.divider()

    # 履歴への保存（1問につき1回だけ記録する）
    if not st.session_state.get('scored_this_turn', False):
        record = {
            "問題": current_q['問題文'],
            "詳細": details
        }
        st.session_state.history.append(record)
        st.session_state.scored_this_turn = True

    # =============================================================
    # 8. 次の問題へ（または結果画面へ）進むボタン（結果画面の直下に配置）
    # =============================================================
    # 今が最後の問題かどうかを判定する
    is_last_question = (st.session_state.index == len(chapter_df) - 1)
    
    # 最後の問題なら「結果を見る」、そうでないなら「次の問題へ進む」
    button_text = "📝 結果を見る ➔" if is_last_question else "次の問題へ進む ➔"

    if st.button(button_text, type="primary", use_container_width=True):
        st.session_state.index += 1
        st.session_state.answered = False
        st.session_state.scored_this_turn = False
        st.session_state.temp_inputs = {}
        st.rerun()