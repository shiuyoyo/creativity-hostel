import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI
from challenge_page import show_challenge_page
from google_sheet_sync import write_to_google_sheet

st.set_page_config(page_title="Questo - Creativity Assistant", layout="centered")

# 🔁 接收網址中的 page=? 參數
query_params = st.query_params
if "page" in query_params and query_params["page"].isdigit():
    st.session_state.page = int(query_params["page"])

titles = {
    1: {"E": "🏁 Event Challenge Description", "C": "🏁 活動挑戰說明"},
    2: {"E": "💡 Initial Idea Generation", "C": "💡 初步構想發想"},
    3: {"E": "💬 Chat with GPT", "C": "💬 與 ChatGPT 真實對話"},
    4: {"E": "📝 Submit Final Creative Ideas", "C": "📝 整合創意成果"},
    5: {"E": "🎯 Feedback Questionnaire", "C": "🎯 問卷調查"},
}

# ✅ 完整的語言文字字典
ui_texts = {
    # 第2頁 - 初步構想
    "idea_input_label": {
        "E": "To win the competition, what are three of the most creative ideas you can think of?",
        "C": "競賽奪冠：你能想出的三個最具創意的點子是什麼？"
    },
    "idea_warning": {
        "E": "⚠️ Please enter your ideas first!",
        "C": "⚠️ 請先輸入構想內容！"
    },

    # 第3頁 - ChatGPT對話
    "gpt_input_label": {
        "E": "To spark your imagination, start by asking ChatGPT some questions about the hotel towel challenge below. See what ideas and insights you can gain, then use that inspiration to propose three more creative ideas.",
        "C": "為了激發你的想像力，請先針對下方的飯店毛巾挑戰向 ChatGPT 提出一些問題。看看你能獲得哪些靈感與洞察."
    },
    "gpt_submit_button": {
        "E": "Submit to ChatGPT",
        "C": "送出給 ChatGPT"
    },
    "gpt_api_error": {
        "E": "⚠️ Please set OPENAI_API_KEY in Streamlit Secrets",
        "C": "⚠️ 請在 Streamlit Secrets 設定 OPENAI_API_KEY"
    },
    "gpt_response_error": {
        "E": "OpenAI response error: {error}",
        "C": "OpenAI 回應錯誤：{error}"
    },
    "gpt_system_prompt": {
        "E": """You are an AI teaching assistant helping students with a class activity about hotel sustainability and creativity.

Activity context:
You are participating in a competition aimed at finding the best ideas for a hotel located in an urban business district to find good uses for the waste it generates. The hotel is situated next to a hospital, a convention center, and a major tourist attraction. Its guests are mainly composed of: (1) Business travelers, (2) Convention attendees, (3) Friends and families of patients, and (4) Tourists. Students are required to propose creative ideas based on the item: "Old towels to be disposed of." Winning ideas should transform hotel waste into something that delights guests and be creative.

Your role:
- Answer questions related to this hotel activity, sustainability, hospitality, or creative problem-solving.
- If a question is unrelated to hotels, hospitality, or this activity, politely redirect the student back to the activity instead of answering.""",

        "C": """你是一位協助學生進行旅館創意活動的 AI 助教。

活動背景：
這是一個關於旅館永續發展的競賽活動。旅館位於城市商業區，鄰近醫院、會議中心與主要觀光景點，住客主要為：(1) 商務旅客、(2) 會議參加者、(3) 病患的親友、(4) 觀光客。學生需針對「即將丟棄的舊毛巾」提出最具創意的再利用方案，讓廢棄物能讓顧客感到驚喜。

你的角色：
- 回答與旅館、餐旅業、永續發展或創意思考相關的問題。
- 若學生提問與旅館活動無關，請禮貌地引導他們回到活動主題，而非直接回答。"""
    },

    # 第4頁 - 最終創意
    "final_idea_prompt": {
        "E": "Based on your experience and exploration, what are the three most creative ideas you can come up with?",
        "C": "根據您的體驗與探索，您能想到的三個最具創意的想法是什麼？"
    },
    "final_idea_submit": {
        "E": "Submit Final Ideas",
        "C": "送出最終創意"
    },
    "final_idea_success": {
        "E": "✅ Final ideas saved! Please continue to complete the questionnaire",
        "C": "✅ 最終創意已儲存！請繼續完成問卷"
    },

    # 第5頁 - 問卷
    "survey_submit": {
        "E": "📩 Submit Questionnaire",
        "C": "📩 送出問卷"
    },
    "survey_success": {
        "E": "✅ Thank you for completing the questionnaire and this task!",
        "C": "✅ 感謝您填寫問卷並完成本次任務！"
    },
    "survey_backup_warning": {
        "E": "⚠️ Google Sheet backup failed: {error}",
        "C": "⚠️ Google Sheet 備份失敗：{error}"
    },

    # 第6頁 - 教師報表
    "admin_title": {
        "E": "🔒 Teacher Report Dashboard",
        "C": "🔒 教師後台報表"
    },
    "admin_password_prompt": {
        "E": "Please enter teacher password to view reports",
        "C": "請輸入教師密碼以檢視報表"
    },
    "admin_password_warning": {
        "E": "Please enter the correct password to access teacher page",
        "C": "請輸入正確密碼以進入教師頁面"
    },
    "admin_login_success": {
        "E": "Login successful ✅ Welcome to the teacher report page!",
        "C": "登入成功 ✅ 歡迎使用教師報表頁！"
    },
    "admin_no_data_error": {
        "E": "⚠️ Unable to read data, please confirm Database.xlsx exists",
        "C": "⚠️ 無法讀取資料，請確認是否有正確的 Database.xlsx"
    },
    "admin_no_records": {
        "E": "Currently no interaction records. Please confirm at least one student has submitted content.",
        "C": "目前尚無任何互動紀錄。請確認至少有一位學生提交過內容。"
    },
    "admin_export_excel": {
        "E": "📥 Export Excel",
        "C": "📥 匯出 Excel"
    },
    "admin_export_pdf": {
        "E": "📄 Download Integrated Report (PDF)",
        "C": "📄 下載整合報表（PDF）"
    },
    "admin_download_pdf": {
        "E": "📥 Click to Download PDF",
        "C": "📥 點我下載 PDF"
    },

    # 通用按鈕
    "next_button": {
        "E": "Next",
        "C": "下一頁"
    },
    "back_button": {
        "E": "Back",
        "C": "上一頁"
    },
    "next_back_button": {
        "E": "Next / 下一頁",
        "C": "下一頁 / Next"
    },
    "back_next_button": {
        "E": "Back / 上一頁",
        "C": "上一頁 / Back"
    }
}

if 'page' not in st.session_state:
    st.session_state.page = 1

if 'user_id' not in st.session_state:
    st.session_state.user_id = f"User_{datetime.now().strftime('%H%M%S')}"

if 'gpt_chat' not in st.session_state:
    st.session_state.gpt_chat = []

if 'language' not in st.session_state:
    st.session_state.language = "English"

if 'maintenance_mode' not in st.session_state:
    st.session_state.maintenance_mode = False

st.markdown(
    "<div style='text-align: right; font-size: 0.9em;'>🔐 <a href='?page=6'>教師報表頁</a></div>",
    unsafe_allow_html=True
)

st.selectbox(
    "Choose your language / 選擇語言",
    ["English", "中文"],
    index=0 if st.session_state.language == "English" else 1,
    key="language",
    disabled=(st.session_state.page > 1)
)

lang_code = "E" if st.session_state.language == "English" else "C"

def next_page():
    st.session_state.page += 1

def prev_page():
    st.session_state.page -= 1

# ── Page 1: Challenge Description ──────────────────────────────────────────
if st.session_state.page == 1:
    show_challenge_page(lang_code, next_page)
    st.button("下一頁 / Next", on_click=next_page)

# ── Page 2: Initial Idea Generation ────────────────────────────────────────
elif st.session_state.page == 2:
    st.title(titles[st.session_state.page][lang_code])

    if 'activity_warning' not in st.session_state:
        st.session_state.activity_warning = False

    activity = st.text_area(ui_texts["idea_input_label"][lang_code], value=st.session_state.get("activity", ""))

    if activity.strip():
        st.session_state.activity_warning = False

    if st.button(ui_texts["next_back_button"][lang_code]):
        if activity.strip() == "":
            st.session_state.activity_warning = True
        else:
            st.session_state.activity = activity
            next_page()

    if st.session_state.activity_warning:
        st.warning(ui_texts["idea_warning"][lang_code])

    st.button(ui_texts["back_next_button"][lang_code], on_click=prev_page)

# ── Page 3: Chat with GPT ───────────────────────────────────────────────────
elif st.session_state.page == 3:
    st.title(titles[st.session_state.page][lang_code])

    msg = st.text_input(ui_texts["gpt_input_label"][lang_code], key="gpt_input")

    if st.button(ui_texts["gpt_submit_button"][lang_code]):
        if "OPENAI_API_KEY" not in st.secrets:
            st.error(ui_texts["gpt_api_error"][lang_code])
        else:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            try:
                history = [{"role": "system", "content": ui_texts["gpt_system_prompt"][lang_code]}]
                for role, txt in st.session_state.gpt_chat:
                    history.append({"role": "user" if role == "user" else "assistant", "content": txt})
                history.append({"role": "user", "content": msg})

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=history
                )
                reply = response.choices[0].message.content
                st.session_state.gpt_chat.append(("user", msg))
                st.session_state.gpt_chat.append(("gpt", reply))
            except Exception as e:
                st.error(ui_texts["gpt_response_error"][lang_code].format(error=e))

    for role, txt in st.session_state.gpt_chat:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.write(txt)

    st.button(ui_texts["next_back_button"][lang_code], on_click=next_page)
    st.button(ui_texts["back_next_button"][lang_code], on_click=prev_page)

# ── Page 4: Final Creative Ideas ────────────────────────────────────────────
elif st.session_state.page == 4:
    st.title(titles[st.session_state.page][lang_code])

    final_ideas = st.text_area(ui_texts["final_idea_prompt"][lang_code])

    if st.button(f"{ui_texts['final_idea_submit'][lang_code]} / Submit Final Ideas", key="submit_final_idea"):
        st.session_state.final_idea = final_ideas
        st.success(ui_texts["final_idea_success"][lang_code])

    st.button(ui_texts["back_next_button"][lang_code], on_click=prev_page, key="back_from_final")
    st.button(ui_texts["next_back_button"][lang_code], on_click=next_page)

# ── Page 5: Survey ──────────────────────────────────────────────────────────
# ── Page 5: Survey ──────────────────────────────────────────────────────────
elif st.session_state.page == 5:
    questionnaire_data = {
        "title": {
            "E": " Research Questionnaire",
            "C": " 研究問卷調查"
        },
        "scale_options": {
            "E": [
                "1: Strongly disagree",
                "2: Disagree",
                "3: Slightly disagree",
                "4: Neutral",
                "5: Slightly agree",
                "6: Agree",
                "7: Strongly agree"
            ],
            "C": [
                "1: 非常不同意",
                "2: 不同意",
                "3: 有點不同意",
                "4: 普通",
                "5: 有點同意",
                "6: 同意",
                "7: 非常同意"
            ]
        },
        "sections": {
            "E": {
                "demographics": {
                    "title": "Section 1: Demographics",
                    "questions": [
                        {"text": "Gender:", "type": "radio", "options": ["Male", "Female", "Prefer not to say"], "key": "gender"},
                        {"text": "Year of Study:", "type": "radio", "options": ["2nd Year", "3rd Year", "4th Year", "Graduate"], "key": "year_study"},
                        {"text": "Major:", "type": "radio", "options": ["Hospitality", "Tourism", "Culinary Arts", "Other"], "key": "major"},
                        {"text": "Prior Experience with Generative AI:", "type": "radio", "options": ["Never used", "Novice", "Intermediate", "Advanced"], "key": "ai_experience"}
                    ]
                },
                "problem_solving": {
                    "title": "Section 2: Your Problem-Solving Style",
                    "questions": [
                        "I feel that I am good at generating novel ideas for hospitality problems.",
                        "I have confidence in my ability to solve problems creatively.",
                        "I have a knack for further developing the ideas of others.",
                        "To ensure that you are paying attention to the questions, please select \"Strongly Disagree\" (1) for this item.",
                        "I am good at finding creative solutions to complex problems.",
                        "I suggest new ways to achieve goals or objectives.",
                        "I feel confident in my ability to ask insightful questions."
                    ]
                },
                "ai_experience_section": {
                    "title": "Section 3: Your Experience Using the AI Tool",
                    "questions": [
                        "Using Generative AI improves my performance in solving the assigned case study.",
                        "Generative AI enables me to formulate questions more quickly than I could alone.",
                        "I find Generative AI useful for generating a wider variety of questions.",
                        "Using Generative AI makes it easier to understand the core problem.",
                        "Overall, I find Generative AI to be useful in my learning process.",
                        "My interaction with the AI Questioning Support Tool is clear and understandable.",
                        "It is easy for me to become skillful at using Generative AI.",
                        "Technology in hospitality is advancing rapidly.\nTo show that you are reading the statements carefully, please ignore the scale and select \"Neutral\" (4) for this question.",
                        "I find Generative AI easy to interact with (e.g., the chat interface is intuitive).",
                        "Getting Generative AI to provide the help I needed was easy.",
                        "I did not require a lot of mental effort to learn how to operate Generative AI."
                    ]
                },
                "outcomes": {
                    "title": "Section 4: Project Outcomes & Reflection",
                    "questions": [
                        "Generative AI helped me generate a large number of questions regarding the problem.",
                        "I was able to come up with more solutions than usual with the help of Generative AI.",
                        "Generative AI helped me see the problem from different angles/perspectives.",
                        "Generative AI's suggestions helped me break away from my initial, fixed assumptions.",
                        "In order to verify the quality of our data, please select \"Strongly Agree\" (7) for this statement.",
                        "I was able to switch between different types of questions (e.g., strategic vs.\noperational) easily.",
                        "The questions I formulated with Generative AI were unique and innovative.",
                        "Generative AI helped me discover ideas I would never have thought of on my own.",
                        "The final solution I proposed was novel compared to standard solutions."
                    ]
                },
                "future": {
                    "title": "Section 5: Future Outlook",
                    "questions": [
                        "Assuming I have access to this AI tool, I intend to use it for future class assignments.",
                        "I would recommend this AI Questioning Support Tool to other hospitality students."
                    ]
                }
            },
            "C": {
                "demographics": {
                    "title": "第一部分：基本資料",
                    "questions": [
                        {"text": "生理性別：", "type": "radio", "options": ["男", "女", "不願透露"], "key": "gender"},
                        {"text": "年級：", "type": "radio", "options": ["大二", "大三", "大四", "研究所"], "key": "year_study"},
                        {"text": "主修科系：", "type": "radio", "options": ["餐旅", "觀光", "廚藝", "其他"], "key": "major"},
                        {"text": "生成式 AI (如 ChatGPT) 使用經驗：", "type": "radio", "options": ["從未用過", "初學者 (偶爾嘗試)", "中等程度 (曾用於作業或日常事務)", "進階使用者 (經常使用並熟悉提示詞技巧)"], "key": "ai_experience"}
                    ]
                },
                "problem_solving": {
                    "title": "第二部分：您的問題解決風格",
                    "questions": [
                        "覺得自己擅長針對餐旅業的問題提出新穎的想法。",
                        "我有信心能創造性地解決問題。",
                        "我擅長延伸或進一步發展他人的想法。",
                        "為了確保您有仔細閱讀題目，請在本題選擇「非常不同意」(1)。",
                        "我擅長為複雜的問題找到創新的解決方案。",
                        "我會提出新的方法來達成目標。",
                        "我有信心能提出具洞察力的問題。"
                    ]
                },
                "ai_experience_section": {
                    "title": "第三部分：您使用 AI 工具的經驗",
                    "questions": [
                        "使用 生成式AI改善了我解決個案研究的表現。",
                        "這個 生成式AI讓我能比自己單獨作業時更快擬定問題。",
                        "我發現生成式AI對於產生「更多樣化」的問題很有用。",
                        "使用生成式AI讓我更容易理解核心問題所在。",
                        "整體而言，我覺得生成式AI對我的學習過程很有用。",
                        "我與 生成式AI的互動過程是清晰易懂的。",
                        "我很容易就能熟練地使用生成式AI。",
                        "餐旅業的科技發展相當迅速。為了證明您有詳閱這些敘述，請忽略量表選項，直接在本題選擇「普通」(4)。",
                        "我覺得生成式AI很容易互動（例如：聊天介面很直觀）。",
                        "我能輕鬆透過生成式AI獲得我需要的協助。",
                        "我不需要花費太多心力去學習如何操作生成式AI。"
                    ]
                },
                "outcomes": {
                    "title": "第四部分：成果與反思",
                    "questions": [
                        "生成式AI幫助我針對問題產生了大量的提問（流暢力）。",
                        "在 生成式AI的協助下，我能比平常提出更多的解決方案。",
                        "生成式AI幫助我從不同的角度或觀點來看待問題（變通力）。",
                        "生成式AI的建議幫助我打破了最初的既定假設或固著觀點。",
                        "為了驗證我們資料的品質，請在本題直接選擇「非常同意」(7)。",
                        "我能輕鬆地在不同類型的問題（例如：策略性 vs.\n營運性）之間切換。",
                        "我透過生成式AI擬定的問題是獨特且創新的（獨創力）。",
                        "生成式AI幫助我發現了一些我自己絕對想不到的想法。",
                        "與標準答案相比，我提出的最終解決方案相當新穎。"
                    ]
                },
                "future": {
                    "title": "第五部分：未來展望",
                    "questions": [
                        "假設我能使用生成式AI，我打算在未來的課堂作業中使用它。",
                        "我會向其他餐旅系學生推薦生成式AI。"
                    ]
                }
            }
        }
    }

    # 讓 validation 失敗後自動滑到最上方
    if st.session_state.get("scroll_to_top", False):
        st.markdown(
            """
            <script>
                window.scrollTo({top: 0, behavior: 'smooth'});
            </script>
            """,
            unsafe_allow_html=True
        )
        st.session_state.scroll_to_top = False

    st.title(questionnaire_data["title"][lang_code])
    st.markdown(f"**Scale: {' | '.join(questionnaire_data['scale_options'][lang_code])}**")

    responses = {}
    scale_options = questionnaire_data["scale_options"][lang_code]
    missing_fields = []

    def show_required_warning(question_text):
        st.markdown(
            f"<div style='color:#d32f2f; font-weight:600; margin-top:-0.35rem; margin-bottom:0.6rem;'>❗ 此題尚未作答 / This item is required</div>",
            unsafe_allow_html=True
        )
        missing_fields.append(question_text)

    # Section 1: Demographics
    st.subheader(questionnaire_data["sections"][lang_code]["demographics"]["title"])

    for q_data in questionnaire_data["sections"][lang_code]["demographics"]["questions"]:
        selected_demo = st.radio(
            q_data["text"],
            q_data["options"],
            index=None,
            key=f"demo_{q_data['key']}"
        )

        responses[q_data["key"]] = selected_demo

        if selected_demo is None:
            show_required_warning(q_data["text"])

    # 共用 Likert section render
    def render_likert_section(section_key, response_prefix, key_prefix):
        st.subheader(questionnaire_data["sections"][lang_code][section_key]["title"])

        for i, question in enumerate(questionnaire_data["sections"][lang_code][section_key]["questions"], start=1):
            selected_option = st.radio(
                question,
                scale_options,
                index=None,
                key=f"{key_prefix}_{i}"
            )

            if selected_option is None:
                responses[f"{response_prefix}_{i}"] = None
                show_required_warning(question)
            else:
                responses[f"{response_prefix}_{i}"] = int(selected_option.split(":")[0])

    # Section 2–5
    render_likert_section("problem_solving", "problem_solving", "ps")
    render_likert_section("ai_experience_section", "ai_experience", "ai_exp")
    render_likert_section("outcomes", "outcomes", "outcomes")
    render_likert_section("future", "future", "future")

    if st.button(ui_texts["survey_submit"][lang_code], key="submit_survey_final"):
        unanswered_items = [q for q in missing_fields if q]

        if unanswered_items:
            st.session_state.scroll_to_top = True
            preview_missing = " / ".join(unanswered_items[:3])

            if lang_code == "E":
                st.error(
                    f"❗ Please complete all questionnaire items before submitting.\n\n"
                    f"Unanswered items: {len(unanswered_items)}\n"
                    f"Examples: {preview_missing}"
                )
            else:
                st.error(
                    f"❗ 請先完成所有問卷題目再送出。\n\n"
                    f"尚未填寫：{len(unanswered_items)} 題\n"
                    f"例如：{preview_missing}"
                )

            st.rerun()

        try:
            df = pd.read_excel("Database.xlsx")
        except Exception:
            df = pd.DataFrame()

        final_row = {
            "時間戳記": datetime.now().isoformat(),
            "使用者編號": st.session_state.user_id,
            "語言": st.session_state.language,
            "初步構想": st.session_state.get("activity", ""),
            "最終構想": st.session_state.get("final_idea", "")
        }

        # GPT 對話（問題 + 回覆）
        gpt_idx = 1
        for role, text in st.session_state.get("gpt_chat", []):
            if role == "user":
                final_row[f"GPT 問題{gpt_idx}"] = text
            else:
                final_row[f"GPT 回覆{gpt_idx}"] = text
                gpt_idx += 1

        # 問卷結果
        final_row.update(responses)

        df = pd.concat([df, pd.DataFrame([final_row])], ignore_index=True)
        df.to_excel("Database.xlsx", index=False)

        st.success(ui_texts["survey_success"][lang_code])

        try:
            from google_sheet_sync import write_to_google_sheet
            write_to_google_sheet(final_row)
        except Exception as e:
            st.warning(ui_texts["survey_backup_warning"][lang_code].format(error=e))
# ── Page 6: Teacher Dashboard ───────────────────────────────────────────────
elif st.session_state.page == 6:
    st.title(ui_texts["admin_title"][lang_code])

    PASSWORD = "!@#$123456"
    pw = st.text_input(ui_texts["admin_password_prompt"][lang_code], type="password", key="admin_pw")

    if pw != PASSWORD:
        st.warning(ui_texts["admin_password_warning"][lang_code])
        st.stop()

    st.success(ui_texts["admin_login_success"][lang_code])

    try:
        df = pd.read_excel("Database.xlsx")
    except:
        st.error(ui_texts["admin_no_data_error"][lang_code])
        st.stop()

    if df.empty:
        st.warning(ui_texts["admin_no_records"][lang_code])
    else:
        st.dataframe(df)

        st.download_button(
            ui_texts["admin_export_excel"][lang_code],
            data=open("Database.xlsx", "rb").read(),
            file_name="Database.xlsx"
        )

        from io import BytesIO
        from fpdf import FPDF

        if st.button(ui_texts["admin_export_pdf"][lang_code], key="dl_pdf"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Creativity Activity Summary Report", ln=True, align="C")
            pdf.ln(10)

            for idx, row in df.iterrows():
                pdf.set_font("Arial", "B", 11)
                pdf.cell(200, 8, f"User ID: {row.get('使用者編號', 'N/A')} | Time: {row.get('時間戳記', '')}", ln=True)
                pdf.set_font("Arial", "", 10)
                for col in df.columns:
                    if col not in ["使用者編號", "時間戳記"]:
                        value = str(row.get(col, "")).replace("\n", "\n")
                        pdf.multi_cell(0, 6, f"{col}: {value}")
                pdf.ln(5)

            buffer = BytesIO()
            pdf.output(buffer)
            pdf_bytes = buffer.getvalue()

            st.download_button(
                ui_texts["admin_download_pdf"][lang_code],
                data=pdf_bytes,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
