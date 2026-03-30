import streamlit as st
import numpy as np
import plotly.graph_objects as go
import json
import datetime

st.set_page_config(page_title="Helical Tube Heat Exchanger Designer", layout="wide")
st.title("플랜트 공정 설계: Helical Tube Heat Exchanger 최적화")
st.markdown("---")

# =========================================================
# [A] 글로벌 상태(Session State) 초기화
# =========================================================
init_state = {
    'tag_no': 'HE-101', 
    'tube_fluid_name': 'Process Slurry',
    'shell_fluid_name': 'Hot Water / Steam',
    'fluid_type': "Liquid (뉴턴 유체 - 물, 오일 등)",
    't_rho': 998.0, 't_cp': 4180.0, 't_k': 0.6, 't_mu': 1.0, 
    's_rho': 998.0, 's_mu': 1.0, 's_cp': 4180.0, 's_k': 0.6,
    'rheology_model': "Power-law (멱법칙)",
    'tau_y': 5.0, 'plastic_visc': 0.05,
    'consistency_k': 0.1, 'flow_index_n': 0.8,
    'm_hot': 5000.0, 'm_cold': 8000.0,
    'T_hot_in': 30.0, 'T_hot_out': 80.0,
    'T_cold_in': 120.0, 'T_cold_out': 90.0,
    'allowable_dp_tube': 1.5, 'allowable_dp_shell': 0.5,
    'N_p': 3, 
    'd_o': 25.4, 't_thick': 2.11, 'D_c': 400.0, 'pitch': 50.0, 'D_s': 500.0,
    'shell_thick': 10.0,
    'D_mandrel': 350.0, 
    'tube_material': 'Stainless Steel 316 (k=16)', 'tube_k_wall': 16.0,
    'R_fi': 0.000176, 'R_fo': 0.000176,
    'overdesign_pct': 10.0,
    'design_p_shell': 10.0, 'allow_s_shell': 137.9, 'joint_e': 0.85, 'ca_shell': 3.0,
    'orientation': 'Vertical (수직형)'
}

for k, v in init_state.items():
    if k not in st.session_state:
        st.session_state[k] = v

def apply_json():
    json_str = st.session_state['json_input_text']
    if not json_str.strip():
        st.warning("JSON 데이터를 입력하십시오.")
        return
    try:
        parsed_data = json.loads(json_str)
        for k in init_state.keys():
            if k in parsed_data:
                st.session_state[k] = parsed_data[k]
        st.success(f"✅ 설계 데이터(Tag: {st.session_state.get('tag_no')}) 로드 완료.")
    except Exception as e:
        st.error(f"🚨 데이터 로드 실패: {e}")

# =========================================================
# [B] 환경설정 및 사이드바
# =========================================================
with st.sidebar:
    st.header("📋 Document Control")
    st.text_input("Item Tag No.", key='tag_no')
    st.markdown("---")
    st.header("💾 설계 시나리오 (Save/Load)")
    current_tag = st.session_state.get('tag_no', 'HE-101')
    current_data = {k: st.session_state[k] for k in init_state.keys()}
    filename = f"{current_tag}_design.json"
    st.download_button(f"📥 '{filename}' 다운로드", json.dumps(current_data, indent=4), file_name=filename, mime="application/json")
    st.text_area("JSON Load:", value="", key='json_input_text', height=150, help="여기에 JSON 텍스트를 붙여넣고 아래 버튼을 누르십시오.")
    st.button("시나리오 적용 (Load)", on_click=apply_json, use_container_width=True)

st.subheader(f"🏷️ Equipment Tag: **{st.session_state['tag_no']}**")

# =========================================================
# [C] 1. 유체 식별 및 물성치
# =========================================================
st.subheader("1. 유체 식별 및 물성치")
st.radio("Tube 유체 상(Phase) 선택", ["Liquid (뉴턴 유체 - 물, 오일 등)", "Slurry (비뉴턴 유체 - 고농도 혼합물)"], key='fluid_type', horizontal=True)

col_tube, col_shell = st.columns(2)
with col_tube:
    st.markdown("#### **Tube-side (Inner)**")
    st.text_input("유체 명칭", key='tube_fluid_name')
    st.number_input("혼합 밀도 (kg/m³)", key='t_rho', help="일반 액체: 700 - 1000, 슬러리: 1100 - 1800 이상")
    st.number_input("비열 (J/kg·K)", key='t_cp', help="물: 4180, 일반 오일류: 1800 - 2400")
    st.number_input("열전도도 (W/m·K)", key='t_k', help="물: 0.6, 일반 오일류: 0.1 - 0.2")
    if "Liquid" in st.session_state['fluid_type']:
        st.number_input("점도 (cP)", format="%.2f", key='t_mu', help="물(20°C): 1.0 cP, 경질유: 2.0 - 10.0")
    else:
        st.selectbox("유변학 모델", ["Power-law (멱법칙)", "Bingham Plastic (빙햄 가소성)"], key='rheology_model')
        if "Bingham" in st.session_state['rheology_model']:
            st.number_input("항복 응력 (Pa)", key='tau_y', help="펄프/고농도 슬러리: 5 - 50 Pa")
            st.number_input("가소성 점도 (Pa·s)", format="%.4f", key='plastic_visc')
        else:
            st.number_input("점조도 지수 K (Pa·sⁿ)", format="%.4f", key='consistency_k')
            st.number_input("유동 지수 n", step=0.1, key='flow_index_n')

with col_shell:
    st.markdown("#### **Shell-side (Outer)**")
    st.text_input("유체 명칭", key='shell_fluid_name')
    st.number_input("밀도 (kg/m³)", key='s_rho')
    st.number_input("비열 (J/kg·K)", key='s_cp')
    st.number_input("열전도도 (W/m·K)", key='s_k')
    st.number_input("점도 (cP)", format="%.2f", key='s_mu')

st.markdown("---")

# =========================================================
# [D] 2. 공정 운전 조건
# =========================================================
st.subheader("2. 공정 운전 조건 (Energy Balance)")

t_in = st.session_state['T_hot_in']
t_out = st.session_state['T_hot_out']
s_in = st.session_state['T_cold_in']
s_out = st.session_state['T_cold_out']
m_t = st.session_state['m_hot']
m_s = st.session_state['m_cold']

Q_kW = (m_t / 3600.0) * (st.session_state['t_cp'] / 1000.0) * abs(t_in - t_out)
s_cp_kJ = st.session_state['s_cp'] / 1000.0

is_tube_heating = (t_out > t_in)
delta_T_shell = abs(s_in - s_out)
est_m_cold = (Q_kW * 3600.0) / (s_cp_kJ * max(0.1, delta_T_shell)) if delta_T_shell > 0 else 0.0

if is_tube_heating:
    est_T_cold_out = s_in - ((Q_kW * 3600.0) / (max(0.1, m_s) * s_cp_kJ))
    op_mode = "🔥 Heater Mode"
else:
    est_T_cold_out = s_in + ((Q_kW * 3600.0) / (max(0.1, m_s) * s_cp_kJ))
    op_mode = "❄️ Cooler Mode"

col_pc1, col_pc2, col_pc3, col_pc4 = st.columns(4)
with col_pc1:
    st.number_input("Tube 유량 (kg/h)", step=100.0, key='m_hot')
    st.number_input("Shell 유량 (kg/h)", step=100.0, key='m_cold')
    st.caption(f"💡 필요 Shell 유량 추정치: **{est_m_cold:,.0f} kg/h**")
with col_pc2:
    st.number_input("Tube 입구 온도 (°C)", key='T_hot_in')
    st.number_input("Tube 목표 출구 온도 (°C)", key='T_hot_out')
    st.caption(f"**운전 모드: {op_mode}** (Q: {Q_kW:,.1f} kW)")
with col_pc3:
    st.number_input("Shell 입구 온도 (°C)", key='T_cold_in')
    st.number_input("Shell 목표 출구 온도 (°C)", key='T_cold_out')
    st.caption(f"💡 예상 Shell 출구 온도: **{est_T_cold_out:,.1f} °C**")
with col_pc4:
    st.number_input("Tube 허용 ΔP (bar)", 0.1, 10.0, step=0.1, key='allowable_dp_tube', help="TEMA 가이드: 0.5 - 0.7 bar 권장")
    st.number_input("Shell 허용 ΔP (bar)", 0.1, 10.0, step=0.1, key='allowable_dp_shell', help="Coil 외부 유동 특성상 0.3 - 0.5 bar 이내 설계 요망")

if is_tube_heating:
    dT1 = s_in - t_out  
    dT2 = s_out - t_in  
else:
    dT1 = t_in - s_out  
    dT2 = t_out - s_in  

lmtd_error = False
if dT1 == dT2 and dT1 > 0:
    LMTD = dT1
elif dT1 > 0 and dT2 > 0:
    LMTD = (dT1 - dT2) / np.log(dT1 / dT2)
else:
    LMTD = 1.0  
    lmtd_error = True

if lmtd_error:
    st.error("🚨 **열역학 에러 (Temperature Cross):** 열전달이 불가능한 온도 역전 현상이 발생했습니다.")

st.markdown("---")

# =========================================================
# [E] 3. 기하학적 설계 (Geometry Design) - 예외 처리 로직 추가
# =========================================================
st.subheader("3. 기하학적 설계 (Geometry Design)")

st.radio("설치 방향 (Installation Orientation)", ["Vertical (수직형)", "Horizontal (수평형)"], key='orientation', horizontal=True, help="Footprint(바닥 면적) 계산을 위해 장비의 설치 방향을 선택하십시오.")
bbox_placeholder = st.empty()
st.markdown("<br>", unsafe_allow_html=True)

col_g1, col_g2, col_g3, col_g4 = st.columns(4)

with col_g1:
    st.number_input("Parallel Tubes (N_p, 가닥)", 1, 50, step=1, key='N_p', help="유량을 N_p개로 분산시킵니다. N_p가 커지면 Tube 상승각(Lead)이 가팔라집니다.")
    
    do_options = {'3/8" (9.53 mm)': 9.53, '1/2" (12.7 mm)': 12.7, '3/4" (19.05 mm)': 19.05, '1" (25.4 mm)': 25.4, 'Custom (직접 입력)': -1}
    do_keys = list(do_options.keys())
    do_vals = list(do_options.values())
    curr_do = st.session_state.get('d_o', 25.4)
    try: do_idx = do_vals.index(curr_do)
    except ValueError: do_idx = len(do_keys) - 1

    selected_do = st.selectbox("Tube OD (외경)", do_keys, index=do_idx, help="표준: 19.05 mm (3/4\"), 슬러리/고점도: 25.4 mm (1\") 이상 권장")
    if "Custom" in selected_do:
        # 🌟 에러 방지: 과거 JSON의 값이 5~100 사이가 아닐 경우를 대비한 Bounding
        safe_do = max(5.0, min(100.0, float(curr_do)))
        st.session_state['d_o'] = st.number_input("Tube OD 직접 입력 (mm)", 5.0, 100.0, value=safe_do, step=0.1)
    else:
        st.session_state['d_o'] = do_options[selected_do]

    with st.expander("💡 Tube OD(외경) 가이드"):
        st.markdown("| 규격 (inch) | 외경 (mm) | 추천 적용 분야 |\n|:---|:---|:---|\n| **3/8\"** | 9.53 | 초소형 장비용 |\n| **1/2\"** | 12.7 | 일반 컴팩트 설계 |\n| **3/4\"** | 19.05 | 압력 손실과 제작 편의성 균형 (표준) |\n| **1\"** | 25.4 | 슬러리 적용 시 플러깅 방지 권장 |")

    bwg_options = {'BWG 10 (3.40 mm)': 3.40, 'BWG 12 (2.77 mm)': 2.77, 'BWG 14 (2.11 mm)': 2.11, 'BWG 16 (1.65 mm)': 1.65, 'BWG 18 (1.24 mm)': 1.24, 'BWG 20 (0.89 mm)': 0.89, 'BWG 22 (0.71 mm)': 0.71, 'Custom (직접 입력)': -1}
    bwg_keys = list(bwg_options.keys())
    bwg_vals = list(bwg_options.values())
    curr_t = st.session_state.get('t_thick', 2.11)
    try: bwg_idx = bwg_vals.index(curr_t)
    except ValueError: bwg_idx = len(bwg_keys) - 1

    selected_bwg = st.selectbox("Tube Thickness (BWG)", bwg_keys, index=bwg_idx, help="일반적인 산업용 표준은 BWG 14 (2.11 mm) 또는 BWG 16 (1.65 mm) 입니다.")
    if "Custom" in selected_bwg:
        # 🌟 에러 방지: Bounding
        safe_t = max(0.5, min(10.0, float(curr_t)))
        st.session_state['t_thick'] = st.number_input("Tube 두께 직접 입력 (mm)", 0.5, 10.0, value=safe_t, step=0.1)
    else:
        st.session_state['t_thick'] = bwg_options[selected_bwg]

    with st.expander("💡 Tube Thickness(BWG) 가이드"):
        st.markdown("| BWG | mm | 특징 |\n|:---|:---|:---|\n| **10** | 3.40 | 고압/부식성 유체, 좁은 밴딩 |\n| **14** | 2.11 | 산업용 열교환기 표준 두께 |\n| **16** | 1.65 | 범용 표준 (유량/내압 균형) |\n| **20** | 0.89 | 계측기 또는 소구경 튜브용 |")

    d_i = st.session_state['d_o'] - 2 * st.session_state['t_thick']
    if d_i <= 0:
        st.error("🚨 Tube 두께 에러")
    else:
        st.caption(f"✓ 유효 내경 (Tube ID): **{d_i:.2f} mm**")

with col_g2:
    st.number_input("Coil Center Dia. (D_c, mm)", step=10.0, key='D_c', help="Coil 벤딩 시 파열을 막기 위해 Tube OD의 최소 10배 이상 권장")
    st.caption(f"💡 추천 최소값: **{st.session_state['d_o'] * 10.0:.1f} mm**")
    
    min_pitch = st.session_state['d_o']
    st.number_input("Coil Pitch (p, mm)", min_value=float(min_pitch), step=1.0, key='pitch', help="상하로 인접한 서로 다른 Tube 중심 간 수직 거리. p=OD일 경우 코일이 딱 붙습니다.")
    st.caption(f"💡 밀착 제작: **{min_pitch:.1f} mm** / TEMA 여유: **{min_pitch*1.25:.1f} mm**")
    
    mat_dict = {'Stainless Steel 316 (k=16)': 16.0, 'Titanium (k=22)': 22.0, 'Custom (직접 입력)': -1}
    mat_keys = list(mat_dict.keys())
    mat_vals = list(mat_dict.values())
    curr_k = st.session_state.get('tube_k_wall', 16.0)
    try: mat_idx = mat_vals.index(curr_k)
    except ValueError: mat_idx = len(mat_keys) - 1

    selected_mat = st.selectbox("Tube Material", mat_keys, index=mat_idx)
    if "Custom" in selected_mat:
        st.session_state['tube_k_wall'] = st.number_input("열전도도 입력", value=float(curr_k))
    else:
        st.session_state['tube_k_wall'] = mat_dict[selected_mat]

with col_g3:
    st.number_input("Mandrel OD (mm)", step=5.0, key='D_mandrel', help="Coil 내측 공간을 채워 Shell 유체의 바이패스를 막는 코어 기둥입니다.")
    rec_mandrel = max(10.0, st.session_state['D_c'] - st.session_state['d_o'] - 10.0)
    st.caption(f"💡 추천 최적값: **{rec_mandrel:.1f} mm** (Coil 내측 직경에서 조립/용접 여유 10mm 제외)")
    
    inner_clearance_rad = ((st.session_state['D_c'] - st.session_state['d_o']) - st.session_state['D_mandrel']) / 2.0
    if inner_clearance_rad < 0:
        st.error(f"🚨 간섭! Mandrel이 Coil을 파고듭니다 ({-inner_clearance_rad:.1f} mm)")
    
    ds_options = {
        'NPS 8" Pipe (ID: 202.7 mm)': 202.7,
        'NPS 10" Pipe (ID: 254.5 mm)': 254.5,
        'NPS 12" Pipe (ID: 304.8 mm)': 304.8,
        'NPS 14" Pipe (ID: 336.6 mm)': 336.6,
        'NPS 16" Pipe (ID: 387.4 mm)': 387.4,
        'NPS 18" Pipe (ID: 438.2 mm)': 438.2,
        'NPS 20" Pipe (ID: 489.0 mm)': 489.0,
        'NPS 24" Pipe (ID: 590.6 mm)': 590.6,
        'Custom (Rolled Plate, 직접입력)': -1
    }
    ds_keys = list(ds_options.keys())
    ds_vals = list(ds_options.values())
    curr_ds = st.session_state.get('D_s', 500.0)
    try: ds_idx = ds_vals.index(curr_ds)
    except ValueError: ds_idx = len(ds_keys) - 1

    selected_ds = st.selectbox("Shell ID (mm)", ds_keys, index=ds_idx, help="NPS 24인치 이하 중소형은 표준 파이프 사용이 원가에 유리하며, 대형은 50mm 단위로 압연 제작합니다.")
    if "Custom" in selected_ds:
        # 🌟 에러 방지: 과거 JSON의 D_s 값이 min/max 범위를 벗어나 앱이 터지는 현상을 막는 Bounding 로직 🌟
        safe_ds = max(200.0, min(5000.0, float(curr_ds)))
        st.session_state['D_s'] = st.number_input("Shell ID 직접 입력 (50mm 단위 권장)", 200.0, 5000.0, value=safe_ds, step=50.0)
    else:
        st.session_state['D_s'] = ds_options[selected_ds]

    rec_Ds = st.session_state['D_c'] + st.session_state['d_o'] + 40.0
    st.caption(f"💡 추천 최소값: **{rec_Ds:.1f} mm** (Coil 외경에서 열팽창/조립 여유 40mm 확보)")

    outer_clearance_rad = (st.session_state['D_s'] - (st.session_state['D_c'] + st.session_state['d_o'])) / 2.0
    if outer_clearance_rad < 0:
        st.error(f"🚨 간섭! Coil이 Shell을 뚫고 나갑니다 ({-outer_clearance_rad:.1f} mm)")

    with st.expander("💡 상업용 Shell 규격 가이드"):
        st.markdown("""
        **1. 중소형 쉘 (NPS 24인치 이하)**
        원가 절감을 위해 시중에서 유통되는 **Seamless / ERW Pipe**를 절단하여 쉘로 사용합니다. 위 드롭다운의 규격(Sch 40 기준 내경)을 선택하십시오.
        
        **2. 대형 쉘 (Custom Rolled Plate)**
        24인치를 초과하는 거대한 쉘은 철판(Plate)을 롤러로 말아서 용접 제작합니다. 철판 로스(Loss)를 최소화하기 위해 내경을 **50 mm 단위 (예: 800, 850, 900)**로 설정하는 것이 관례입니다.
        """)

with col_g4:
    st.markdown("#### 🛡️ 오염계수 및 여유율")
    st.number_input("Tube Fouling Factor (R_fi)", 0.0, 0.02, format="%.6f", key='R_fi', help="Tube 내부 유체의 스케일 저항값")
    st.number_input("Shell Fouling Factor (R_fo)", 0.0, 0.02, format="%.6f", key='R_fo', help="Tube 외부 스케일 저항값. 세척이 어려워 보수적으로 적용.")
    st.number_input("Overdesign (%)", 0.0, 100.0, step=1.0, key='overdesign_pct', help="계산된 필요 면적에 추가할 설계 안전 여유율 (통상 10~20%)")
    
    with st.expander("💡 TEMA Fouling 레퍼런스"):
        st.markdown("| 유체 | 오염계수 (m²·K/W) |\n|:---|:---|\n| 청정수 | 0.00018 |\n| 냉각수 | 0.00035 |\n| 공정 슬러리 | 0.00150+ |")

st.markdown("---")

# =========================================================
# [F] 4. 기계적 설계 (Mechanical Design)
# =========================================================
st.subheader("4. 기계적 설계 (Mechanical Design - ASME Sec.VIII)")

with st.expander("💡 ASME 기계 설계 가이드 (S, E, C.A.)"):
    st.markdown("""
    **1. 주요 재질별 허용 응력 (S)**
    | 재질 (Material) | ASME 규격 | 허용 응력 (MPa) |
    | :--- | :--- | :--- |
    | **일반 탄소강** | SA-516 Gr.70 | 137.9 |
    | **오스테나이트 스텐레스** | SA-240 304/316 | 115.0 - 137.0 |
    
    **2. 용접 조인트 효율 (E)**
    | RT 검사 수준 | 효율 (E) | 적용 기준 |
    | :--- | :--- | :--- |
    | **Full RT (전면 검사)** | 1.00 | 고압, 맹독성 유체 |
    | **Spot RT (국부 검사)** | 0.85 | 일반적인 Shell 표준 |
    
    **3. 부식 여유 (C.A.)**
    | 재질 및 환경 | C.A. (mm) | 비고 |
    | :--- | :--- | :--- |
    | **스텐레스강** | 0.0 - 1.5 | 부식 없음 가정 |
    | **탄소강 (일반)** | 3.0 | 일반 표준 (1/8 인치) |
    | **탄소강 (슬러리)** | 6.0 | 부식/마모 극심 |
    """)
    
cc1, cc2, cc3, cc4 = st.columns(4)
with cc1:
    st.number_input("Shell 설계 압력 (bar)", step=1.0, key='design_p_shell', help="운전 압력의 110% 또는 +1.5 bar")
with cc2:
    st.number_input("허용 응력 (S, MPa)", step=1.0, key='allow_s_shell', help="재질에 따른 ASME 허용 응력")
with cc3:
    st.number_input("용접 효율 (E)", max_value=1.0, key='joint_e', help="RT 검사 범위 (1.0 또는 0.85)")
with cc4:
    st.number_input("부식 여유 (C.A., mm)", step=0.5, key='ca_shell', help="탄소강 기본 3.0mm")

P_mpa = st.session_state['design_p_shell'] / 10.0
R_mm = st.session_state['D_s'] / 2.0
S_mpa = st.session_state['allow_s_shell']
E_eff = st.session_state['joint_e']
C_A = st.session_state['ca_shell']

t_req = (P_mpa * R_mm) / (S_mpa * E_eff - 0.6 * P_mpa) + C_A
t_final = max(6.0, np.ceil(t_req))
st.session_state['shell_thick'] = t_final
shell_od = st.session_state['D_s'] + 2.0 * t_final

st.info(f"✓ 상업용 Shell Thickness: **{t_final:.0f} mm** 확정 (ASME 이론 두께: {t_req:.2f} mm)")

# =========================================================
# [G] 백그라운드 수력학/열역학 코어 연산
# =========================================================
t_mu_pa = st.session_state.get('t_mu', 1.0) / 1000.0
s_mu_pa = st.session_state.get('s_mu', 1.0) / 1000.0
curvature_ratio = d_i / st.session_state['D_c'] if st.session_state['D_c'] > 0 else 0

m_hot_per_tube = (m_t / 3600.0) / max(1, st.session_state['N_p'])
A_c = np.pi * ((d_i / 1000.0) ** 2) / 4.0 if d_i > 0 else 1e-6
v_tube = m_hot_per_tube / (st.session_state['t_rho'] * A_c)

if "Liquid" in st.session_state['fluid_type']:
    Re = (st.session_state['t_rho'] * v_tube * (max(1e-6, d_i) / 1000.0)) / max(1e-6, t_mu_pa)
    Pr = (st.session_state['t_cp'] * t_mu_pa) / max(1e-6, st.session_state['t_k'])
    De = Re * np.sqrt(max(0, curvature_ratio))
    Re_crit = 2100 * (1.0 + 12.0 * np.sqrt(max(0, curvature_ratio)))
    f_c = (64.0 / max(Re, 1.0) * (1.0 + 0.033 * (np.log10(max(De, 1.0)))**4.0)) if Re < Re_crit else (0.304 / (max(Re, 1.0) ** 0.25) + 0.029 * np.sqrt(max(0, curvature_ratio)))
    Nu_straight = 4.36 if Re < Re_crit else 0.023 * (max(Re, 1.0) ** 0.8) * (Pr ** 0.4)
else:
    n_val = st.session_state['flow_index_n'] if "Power" in st.session_state['rheology_model'] else 1.0
    K_val = st.session_state['consistency_k'] if "Power" in st.session_state['rheology_model'] else st.session_state['plastic_visc']
    D_m_tube = max(1e-6, d_i) / 1000.0
    term1 = st.session_state['t_rho'] * (v_tube ** (2.0 - n_val)) * (D_m_tube ** n_val)
    term2 = (8.0 ** (n_val - 1.0)) * max(K_val, 0.0001) * (((3.0 * n_val + 1.0) / (4.0 * n_val)) ** n_val)
    Re = term1 / term2 if term2 > 0 else 0.0
    mu_app = term1 / (Re * v_tube) if (Re * v_tube) > 0 else 0.001
    Pr = (st.session_state['t_cp'] * mu_app) / max(1e-6, st.session_state['t_k'])
    De = Re * np.sqrt(max(0, curvature_ratio))
    Re_crit = 2100 * (1.0 + 12.0 * np.sqrt(max(0, curvature_ratio)))
    f_c = (64.0 / max(Re, 1.0) * (1.0 + 0.033 * (np.log10(max(De, 1.0)))**4.0)) if Re < Re_crit else (0.304 / (max(Re, 1.0) ** 0.25) + 0.029 * np.sqrt(max(0, curvature_ratio)))
    Nu_straight = 4.36 if Re < Re_crit else 0.023 * (max(Re, 1.0) ** 0.8) * (Pr ** 0.4)

Nu_calc = Nu_straight * (1.0 + 3.5 * curvature_ratio)
h_i = (Nu_calc * st.session_state['t_k']) / (max(1e-6, d_i) / 1000.0)

m_cold_kg_s = m_s / 3600.0
D_s_m = st.session_state['D_s'] / 1000.0
D_man_m = st.session_state['D_mandrel'] / 1000.0
d_o_m = st.session_state['d_o'] / 1000.0

N_p_val = max(1, st.session_state['N_p'])
p_m = st.session_state['pitch'] / 1000.0
D_c_m = st.session_state['D_c'] / 1000.0
Lead_m = p_m * N_p_val
Length_per_Turn = np.sqrt((np.pi * D_c_m)**2 + Lead_m**2) if D_c_m > 0 else 1.0

A_annulus = (np.pi / 4.0) * (D_s_m**2 - D_man_m**2)
A_tube_cross = (np.pi / 4.0) * (d_o_m**2)
A_blocked = N_p_val * A_tube_cross * (Length_per_Turn / max(1e-6, Lead_m))
A_free_flow = max(A_annulus * 0.1, A_annulus - A_blocked)

v_shell = m_cold_kg_s / (st.session_state['s_rho'] * A_free_flow) if A_free_flow > 0 else 0.0

D_e_shell = D_s_m - D_man_m
Re_shell = (st.session_state['s_rho'] * v_shell * D_e_shell) / max(1e-6, s_mu_pa)
Pr_shell = (st.session_state['s_cp'] * s_mu_pa) / max(1e-6, st.session_state['s_k'])
Nu_shell = 0.33 * (max(Re_shell, 1.0) ** 0.6) * (Pr_shell ** 0.33)
h_o = (Nu_shell * st.session_state['s_k']) / max(1e-6, d_o_m)

pitch_ratio = st.session_state['pitch'] / max(1e-6, st.session_state['d_o'])
penalty_factor = 1.0
if pitch_ratio < 1.25:
    penalty_factor = max(0.5, 1.0 - 2.0 * (1.25 - pitch_ratio)) 
h_o = h_o * penalty_factor

R_wall = (d_o_m * np.log(st.session_state['d_o'] / max(1e-6, d_i))) / (2.0 * max(1e-6, st.session_state['tube_k_wall'])) if d_i > 0 else 0
U_calc = 1.0 / ((1.0 / max(h_o, 0.1)) + st.session_state['R_fo'] + R_wall + st.session_state['R_fi'] * (st.session_state['d_o'] / max(1e-6, d_i)) + (st.session_state['d_o'] / max(1e-6, d_i)) * (1.0 / max(h_i, 0.1)))

Area_req = (Q_kW * 1000.0) / (U_calc * LMTD) if not lmtd_error else 0.0
Area_design = Area_req * (1.0 + st.session_state['overdesign_pct'] / 100.0)

Total_Tube_Length = Area_design / (np.pi * d_o_m) if d_o_m > 0 else 0.0
Length_per_Tube = Total_Tube_Length / N_p_val
Turns_per_Tube = Length_per_Tube / Length_per_Turn

dp_tube_bar = (f_c * (Length_per_Tube / (max(1e-6, d_i) / 1000.0)) * (st.session_state['t_rho'] * (v_tube ** 2) / 2.0)) / 100000.0

L_shell_m = Turns_per_Tube * Lead_m
L_shell_mm = L_shell_m * 1000.0
f_s = 0.316 / (max(Re_shell, 1.0)**0.25) 
dp_shell_bar = (f_s * (L_shell_m / max(1e-6, D_e_shell)) * (st.session_state['s_rho'] * (v_shell ** 2) / 2.0)) / 100000.0

# =========================================================
# [H] AI 최적화 제안 (Optimizer)
# =========================================================
opt_best_Dc = None
opt_min_LTT = float('inf')
opt_best_Dm = None
opt_best_Ds = None
opt_p_m = (st.session_state['d_o'] * 1.25) / 1000.0
opt_Lead_m = opt_p_m * N_p_val

for t_Dc in np.arange(st.session_state['d_o'] * 10.0, 3000.0, 10.0):
    t_Dc_m = t_Dc / 1000.0
    t_Dm = max(10.0, t_Dc - st.session_state['d_o'] - 10.0)
    t_Dm_m = t_Dm / 1000.0
    t_Ds = t_Dc + st.session_state['d_o'] + 40.0
    t_Ds_m = t_Ds / 1000.0

    t_A_annulus = (np.pi / 4.0) * (t_Ds_m**2 - t_Dm_m**2)
    t_Length_per_Turn = np.sqrt((np.pi * t_Dc_m)**2 + opt_Lead_m**2) if t_Dc_m > 0 else 1.0
    t_A_blocked = N_p_val * ((np.pi / 4.0) * (d_o_m**2)) * (t_Length_per_Turn / max(1e-6, opt_Lead_m))
    t_A_free = max(t_A_annulus * 0.1, t_A_annulus - t_A_blocked)

    t_v_shell = m_cold_kg_s / (st.session_state['s_rho'] * t_A_free) if t_A_free > 0 else 0.0
    t_Re_shell = (st.session_state['s_rho'] * t_v_shell * (t_Ds_m - t_Dm_m)) / max(1e-6, s_mu_pa)
    t_ho = ((0.33 * (max(t_Re_shell, 1.0) ** 0.6) * (Pr_shell ** 0.33)) * st.session_state['s_k']) / max(1e-6, d_o_m)
    
    t_cr = d_i / t_Dc if t_Dc > 0 else 0
    t_hi = ((Nu_straight * (1.0 + 3.5 * t_cr)) * st.session_state['t_k']) / (max(1e-6, d_i) / 1000.0)
    
    t_U = 1.0 / ((1.0 / max(t_ho, 0.1)) + st.session_state['R_fo'] + R_wall + st.session_state['R_fi'] * (st.session_state['d_o'] / max(1e-6, d_i)) + (st.session_state['d_o'] / max(1e-6, d_i)) * (1.0 / max(t_hi, 0.1)))
    t_Area_req = (Q_kW * 1000.0) / (t_U * LMTD) if not lmtd_error else 0.0
    t_Area_design = t_Area_req * (1.0 + st.session_state['overdesign_pct'] / 100.0)
    
    t_Turns = (t_Area_design / (np.pi * d_o_m * N_p_val)) / (np.sqrt((np.pi * t_Dc_m)**2 + opt_Lead_m**2) if t_Dc_m > 0 else 1.0)
    t_L_shell_m = t_Turns * opt_Lead_m
    t_L_TT = t_L_shell_m + (2.0 * t_Ds_m)
    
    if t_Dc_m < t_L_TT: 
        if t_L_TT < opt_min_LTT:
            opt_min_LTT = t_L_TT
            opt_best_Dc = t_Dc
            opt_best_Dm = t_Dm
            opt_best_Ds = t_Ds

# =========================================================
# [I] 실시간 Bounding Box 렌더링
# =========================================================
Shell_TT_Length_m = L_shell_m + (2.0 * D_s_m) 
Shell_TT_Length_mm = Shell_TT_Length_m * 1000.0
shell_od_m = shell_od / 1000.0

if "Vertical" in st.session_state['orientation']:
    Footprint_Area = (np.pi / 4.0) * (shell_od_m ** 2)
else:
    Footprint_Area = shell_od_m * Shell_TT_Length_m

with bbox_placeholder.container():
    st.markdown("#### 📐 실시간 장비 예상 규격 (Estimated Bounding Box)")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Shell OD (외경)", f"{shell_od:,.1f} mm")
    b2.metric("Coiled Section Height", f"{L_shell_mm:,.0f} mm")
    if Shell_TT_Length_m > 10.0:
        b3.metric("🚨 Shell Length (T/T)", f"{Shell_TT_Length_mm:,.0f} mm", delta="과도한 길이! 배관 불가", delta_color="inverse")
    else:
        b3.metric("Shell Length (T/T)", f"{Shell_TT_Length_mm:,.0f} mm", delta="안정적 구조", delta_color="normal")
    b4.metric("장비 바닥 면적 (Footprint)", f"{Footprint_Area:,.2f} m²", help="설치 방향(Vertical/Horizontal)에 따라 달라집니다.")
    
    if opt_best_Dc:
        st.success(f"💡 **[AI 최적화 제안]** N_p={N_p_val}가닥 기준, 최소 Shell 길이({opt_min_LTT*1000:,.0f} mm)를 달성하는 최적 콤보: **Coil D_c = {opt_best_Dc:,.0f} mm** (이때 D_m={opt_best_Dm:,.0f}, D_s={opt_best_Ds:,.0f}, Pitch={st.session_state['d_o']*1.25:.1f})")
    st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# [J] 5. 상업용 데이터시트 검증 (Datasheet)
# =========================================================
st.markdown("---")
st.subheader("5. 열전달 및 수력학 검증 (Datasheet & Report)")
st.caption(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with st.expander("💡 설계 유속(Velocity) 가이드라인 및 판정 기준"):
    st.markdown("""
    | 유체 경로 | 권장 유속 범위 | 초과/미달 시 발생 문제 |
    | :--- | :--- | :--- |
    | **Tube 측 (액체)** | 1.0 ~ 2.5 m/s | **< 1.0:** 침전물/오염 유발 <br> **> 3.0:** Tube 침식(Erosion) 및 파열 |
    | **Shell 측 (액체)** | 0.3 ~ 1.0 m/s | **< 0.2:** 열전달 사각지대 발생 <br> **> 1.5:** 유체 유발 진동(FIV)으로 코일 파손 |
    """)

if penalty_factor < 1.0:
    st.warning(f"⚠️ **코일 밀착 페널티 적용됨:** Pitch가 기준치(1.25*OD)보다 작아 코일 틈새 사각지대 현상을 반영했습니다. Shell 측 열전달 계수(h_o)가 {(1.0-penalty_factor)*100:.0f}% 삭감되었습니다.")

datasheet_md = f"""
| **Item Tag No.** | **{st.session_state['tag_no']}** | **Type** | Helical Coil Heat Exchanger |
| :--- | :--- | :--- | :--- |
| **Performance Data** | | | |
| Heat Duty (kW) | {Q_kW:,.2f} | Overall U-value (W/m²K) | {U_calc:,.1f} |
| Req. Area / Design Area | {Area_req:,.2f} m² / **{Area_design:,.2f} m²** (+{st.session_state['overdesign_pct']}%) | LMTD (°C) | {LMTD:,.1f} |
| **Process Conditions** | **Tube Side (Inner)** | **Shell Side (Outer)** | |
| Fluid Name | **{st.session_state['tube_fluid_name']}** | **{st.session_state['shell_fluid_name']}** | |
| Total Flow Rate (kg/h) | {st.session_state['m_hot']:,.0f} | {st.session_state['m_cold']:,.0f} | |
| Temp. In / Out (°C) | {st.session_state['T_hot_in']} / {st.session_state['T_hot_out']} | {st.session_state['T_cold_in']} / {st.session_state['T_cold_out']} | |
| Velocity (m/s) | **{v_tube:.2f}** | **{v_shell:.2f}** | |
| Calc. Press. Drop (bar)| **{dp_tube_bar:.3f}** (Allow: {st.session_state['allowable_dp_tube']}) | **{dp_shell_bar:.3f}** (Allow: {st.session_state['allowable_dp_shell']}) | |
| **Mechanical Design** | | | |
| **[Tube]** OD x Thick. (mm) | {st.session_state['d_o']} x {st.session_state['t_thick']} | **[Tube]** Material | {st.session_state['tube_material']} |
| **[Tube]** Parallel Coils (N_p)| **{st.session_state['N_p']} ea** | **[Tube]** Length per Tube | {Length_per_Tube:,.1f} m |
| **[Coil]** Center Dia. (D_c) | {st.session_state['D_c']} mm | **[Coil]** Pitch (Gap) | {st.session_state['pitch']} mm |
| **[Coil]** Turns per Tube | {Turns_per_Tube:,.1f} turns | **[Install]** Orientation | {st.session_state['orientation']} |
| **[Shell]** ID / Mandrel OD | {st.session_state['D_s']} mm / {st.session_state['D_mandrel']} mm | **[Shell]** OD x Thick. (mm) | **{shell_od:.1f} x {st.session_state['shell_thick']:.0f}** |
| **[Shell]** T/T Length (mm) | **{Shell_TT_Length_mm:,.0f} mm** | | |
"""
st.markdown(datasheet_md)

html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{st.session_state['tag_no']} - Heat Exchanger Datasheet</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; margin: 20px; }}
        .header {{ text-align: center; border-bottom: 3px solid #004488; padding-bottom: 10px; margin-bottom: 30px; }}
        h2 {{ margin: 0; color: #004488; font-size: 24px; }}
        .meta-info {{ font-size: 12px; color: #666; text-align: right; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 12px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f7f6; font-weight: bold; color: #333; }}
        .section-title {{ background-color: #004488; color: white; padding: 6px 12px; font-size: 14px; font-weight: bold; }}
        @media print {{
            body {{ margin: 0; padding: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="background-color: #fff3cd; padding: 10px; border: 1px solid #ffeeba; margin-bottom: 20px; font-size: 14px;">
        💡 <b>엔지니어 가이드:</b> 완벽한 PDF를 얻으려면 <code>Ctrl + P</code> (인쇄)를 누른 뒤, 대상을 <b>'PDF로 저장'</b>으로 변경하십시오.
    </div>
    
    <div class="header">
        <h2>COMMERCIAL DATASHEET</h2>
        <p style="margin:5px 0; font-weight:bold;">Helical Coil Heat Exchanger</p>
    </div>
    
    <div class="meta-info">Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    
    <table>
        <tr><td class="section-title" colspan="4">1. General Information</td></tr>
        <tr><th>Item Tag No.</th><td><b>{st.session_state['tag_no']}</b></td><th>Overall U-value</th><td>{U_calc:,.1f} W/m²K</td></tr>
        <tr><th>Heat Duty</th><td>{Q_kW:,.2f} kW</td><th>Req. / Design Area</th><td>{Area_req:,.2f} / <b>{Area_design:,.2f} m²</b> (+{st.session_state['overdesign_pct']}%)</td></tr>
        <tr><th>LMTD</th><td>{LMTD:,.1f} &deg;C</td><th>Operation Mode</th><td>{op_mode}</td></tr>
        
        <tr><td class="section-title" colspan="4">2. Process Conditions</td></tr>
        <tr><th>Parameter</th><th colspan="1">Tube Side (Inner)</th><th colspan="2">Shell Side (Outer)</th></tr>
        <tr><td>Fluid Name</td><td colspan="1">{st.session_state['tube_fluid_name']}</td><td colspan="2">{st.session_state['shell_fluid_name']}</td></tr>
        <tr><td>Flow Rate (kg/h)</td><td colspan="1">{st.session_state['m_hot']:,.0f}</td><td colspan="2">{st.session_state['m_cold']:,.0f}</td></tr>
        <tr><td>Temp. In / Out (&deg;C)</td><td colspan="1">{st.session_state['T_hot_in']} / {st.session_state['T_hot_out']}</td><td colspan="2">{st.session_state['T_cold_in']} / {st.session_state['T_cold_out']}</td></tr>
        <tr><td>Velocity (m/s)</td><td colspan="1">{v_tube:.2f}</td><td colspan="2">{v_shell:.2f}</td></tr>
        <tr><td>Pressure Drop (bar)</td><td colspan="1"><b>{dp_tube_bar:.3f}</b> (Allow: {st.session_state['allowable_dp_tube']})</td><td colspan="2"><b>{dp_shell_bar:.3f}</b> (Allow: {st.session_state['allowable_dp_shell']})</td></tr>
        <tr><td>Fouling Factor</td><td colspan="1">{st.session_state['R_fi']:.6f}</td><td colspan="2">{st.session_state['R_fo']:.6f}</td></tr>
        
        <tr><td class="section-title" colspan="4">3. Mechanical Design (ASME Sec.VIII)</td></tr>
        <tr><th>[Tube] OD x Thick. (mm)</th><td>{st.session_state['d_o']} x {st.session_state['t_thick']}</td><th>[Tube] Material</th><td>{st.session_state['tube_material']}</td></tr>
        <tr><th>[Tube] Parallel Coils (N_p)</th><td>{st.session_state['N_p']} ea</td><th>[Tube] Length per Tube</th><td>{Length_per_Tube:,.1f} m</td></tr>
        <tr><th>[Coil] Center Dia. (D_c)</th><td>{st.session_state['D_c']} mm</td><th>[Coil] Pitch (Gap)</th><td>{st.session_state['pitch']} mm</td></tr>
        <tr><th>[Coil] Turns per Tube</th><td>{Turns_per_Tube:,.1f} turns</td><th>[Install] Orientation</th><td>{st.session_state['orientation']}</td></tr>
        <tr><th>[Shell] ID / Mandrel OD</th><td>{st.session_state['D_s']} mm / {st.session_state['D_mandrel']} mm</td><th>[Shell] OD x Thick. (mm)</th><td>{shell_od:.1f} x {st.session_state['shell_thick']:.0f}</td></tr>
        <tr><th>[Shell] T/T Length (mm)</th><td colspan="3" style="font-size:16px;"><b>{Shell_TT_Length_mm:,.0f} mm</b></td></tr>
    </table>
</body>
</html>
"""

col_dl1, col_dl2 = st.columns([1, 2])
with col_dl1:
    st.download_button(label="📄 Datasheet 다운로드 (HTML/PDF용)", data=html_report, file_name=f"{st.session_state['tag_no']}_Datasheet.html", mime="text/html")
with col_dl2:
    st.info("💡 폰트 에러 없는 PDF 출력을 위해 HTML로 내보냅니다. 브라우저 인쇄(Ctrl+P) 기능을 활용하세요.")

err_msg = []
if lmtd_error: err_msg.append("Temperature Cross (온도 역전) 발생")
if inner_clearance_rad < 0: err_msg.append("Mandrel - Coil 내측 간섭 발생")
if outer_clearance_rad < 0: err_msg.append("Shell - Coil 외측 간섭 발생")
if dp_tube_bar > st.session_state['allowable_dp_tube']: err_msg.append(f"Tube 측 ΔP 초과")
if dp_shell_bar > st.session_state['allowable_dp_shell']: err_msg.append(f"Shell 측 ΔP 초과")
if Shell_TT_Length_m > 10.0: err_msg.append(f"장비 총 길이 10m 초과 (레이아웃 한계)")
if d_i <= 0: err_msg.append("내경(ID) 계산 불가")

if v_tube < 1.0: err_msg.append("Tube 유속 저하 (오염/침전 위험)")
if v_tube > 3.0: err_msg.append("Tube 유속 초과 (침식 위험)")
if v_shell < 0.2: err_msg.append("Shell 유속 저하 (열전달 사각지대 위험)")
if v_shell > 1.5: err_msg.append("Shell 유속 초과 (진동/파손 위험)")

if err_msg:
    st.error("🚨 **Datasheet Warning:** " + " / ".join(err_msg))
else:
    st.success("✅ **Datasheet Validated:** 모든 공정, 수력학, 기계적 제약 조건을 통과했습니다.")

# =========================================================
# [K] 6. 3D 형상 렌더링
# =========================================================
st.markdown("---")
st.subheader("6. 3D 코일 형상 (Schematic Representation)")

if Turns_per_Tube > 0 and Turns_per_Tube < 2000 and d_i > 0 and not lmtd_error:
    fig = go.Figure()
    
    t_max_full = Turns_per_Tube * 2 * np.pi
    coil_height = (Lead_m * 1000.0 / (2 * np.pi)) * t_max_full if Turns_per_Tube > 0 else 1.0
    
    render_turns = min(Turns_per_Tube, 3.0)
    t_max_render = render_turns * 2 * np.pi
    num_t = int(max(render_turns * 40, 50))
    num_theta = 12
    t_vals = np.linspace(0, t_max_render, num_t)
    theta_vals = np.linspace(0, 2 * np.pi, num_theta)
    T_grid, Theta_grid = np.meshgrid(t_vals, theta_vals)
    
    R_c = st.session_state['D_c'] / 2.0
    r_tube = st.session_state['d_o'] / 2.0
    c_val = (Lead_m * 1000.0) / (2 * np.pi)
    denom = np.sqrt(R_c**2 + c_val**2) if (R_c**2 + c_val**2) > 0 else 1.0
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    for i in range(int(N_p_val)):
        angle_offset = i * (2 * np.pi / N_p_val)
        t_shifted = T_grid + angle_offset
        
        C_x = R_c * np.cos(t_shifted)
        C_y = R_c * np.sin(t_shifted)
        C_z = c_val * T_grid
        
        N_x = -np.cos(t_shifted)
        N_y = -np.sin(t_shifted)
        N_z = np.zeros_like(t_shifted)
        
        B_x = (c_val / denom) * np.sin(t_shifted)
        B_y = -(c_val / denom) * np.cos(t_shifted)
        B_z = (R_c / denom) * np.ones_like(t_shifted)
        
        X = C_x + r_tube * (N_x * np.cos(Theta_grid) + B_x * np.sin(Theta_grid))
        Y = C_y + r_tube * (N_y * np.cos(Theta_grid) + B_y * np.sin(Theta_grid))
        Z = C_z + r_tube * (N_z * np.cos(Theta_grid) + B_z * np.sin(Theta_grid))
        
        tube_color = colors[i % len(colors)]
        
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale=[[0, tube_color], [1, tube_color]],
            showscale=False,
            name=f'Coil {i+1} (Real OD)',
            lighting=dict(ambient=0.5, diffuse=0.8, specular=0.5, roughness=0.5),
            hoverinfo='skip'
        ))
        
    if Turns_per_Tube > 3.0:
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[c_val * t_max_render + st.session_state['d_o'] * 2.0],
            mode='text',
            text=["(Coil Rendering Truncated to 3 Turns for Performance)"],
            textposition="top center",
            textfont=dict(color='red', size=14),
            name='Truncation Info',
            hoverinfo='skip'
        ))
        
    z_surf = np.linspace(0, coil_height, 20)
    theta_surf = np.linspace(0, 2*np.pi, 25)
    theta_grid, z_grid = np.meshgrid(theta_surf, z_surf)
    
    x_man = (st.session_state['D_mandrel'] / 2) * np.cos(theta_grid)
    y_man = (st.session_state['D_mandrel'] / 2) * np.sin(theta_grid)
    fig.add_trace(go.Surface(
        x=x_man, y=y_man, z=z_grid, 
        opacity=0.6, 
        colorscale=[[0, '#666666'], [1, '#999999']], 
        showscale=False, name='Mandrel', 
        lighting=dict(ambient=0.5, diffuse=0.8, specular=0.5), hoverinfo='skip'
    ))
    
    x_shell = (st.session_state['D_s'] / 2) * np.cos(theta_grid)
    y_shell = (st.session_state['D_s'] / 2) * np.sin(theta_grid)
    fig.add_trace(go.Surface(x=x_shell, y=y_shell, z=z_grid, opacity=0.08, colorscale='Blues', showscale=False, name='Shell', hoverinfo='skip'))
    
    noz_h = st.session_state['d_o'] * 3.0
    in_x = (st.session_state['D_c'] / 2) * np.cos(0)
    in_y = (st.session_state['D_c'] / 2) * np.sin(0)
    fig.add_trace(go.Scatter3d(x=[in_x, in_x], y=[in_y, in_y], z=[coil_height, coil_height + noz_h], mode='lines', line=dict(color='red', width=12), name='Tube Inlet'))
    out_x = (st.session_state['D_c'] / 2) * np.cos(t_max_full % (2 * np.pi))
    out_y = (st.session_state['D_c'] / 2) * np.sin(t_max_full % (2 * np.pi))
    fig.add_trace(go.Scatter3d(x=[out_x, out_x], y=[out_y, out_y], z=[0, -noz_h], mode='lines', line=dict(color='red', width=12), name='Tube Outlet'))
    
    sh_in_r = st.session_state['D_s'] / 2.0
    fig.add_trace(go.Scatter3d(x=[sh_in_r, sh_in_r + noz_h], y=[0, 0], z=[p_m*1000/2.0, p_m*1000/2.0], mode='lines', line=dict(color='blue', width=12), name='Shell Inlet'))
    fig.add_trace(go.Scatter3d(x=[-sh_in_r, -sh_in_r - noz_h], y=[0, 0], z=[coil_height - p_m*1000/2.0, coil_height - p_m*1000/2.0], mode='lines', line=dict(color='blue', width=12), name='Shell Outlet'))
    
    top_z = coil_height + 50.0
    pos_man = st.session_state['D_mandrel'] / 2.0
    pos_inner_clr = pos_man + inner_clearance_rad / 2.0
    pos_coil = st.session_state['D_c'] / 2.0
    pos_outer_clr = pos_coil + st.session_state['d_o']/2.0 + outer_clearance_rad / 2.0
    pos_shell = st.session_state['D_s'] / 2.0
    
    text_x = [pos_man, pos_inner_clr, pos_coil, pos_outer_clr, pos_shell]
    text_y = [0, 0, 0, 0, 0]
    text_z = [top_z, top_z, top_z, top_z, top_z]
    text_labels = [
        f"Mandrel OD<br>{st.session_state['D_mandrel']}",
        f"Inner Clr.<br>{inner_clearance_rad:.1f}",
        f"Coil D_c {st.session_state['D_c']}<br>(Tube OD {st.session_state['d_o']})",
        f"Outer Clr.<br>{outer_clearance_rad:.1f}",
        f"Shell ID<br>{st.session_state['D_s']}"
    ]
    
    fig.add_trace(go.Scatter3d(
        x=text_x, y=text_y, z=text_z,
        mode='text+markers',
        text=text_labels,
        textposition="top center",
        marker=dict(size=4, color='black'),
        name='Clearance Info',
        hoverinfo='skip'
    ))

    fig.update_layout(scene=dict(xaxis_title='X (mm)', yaxis_title='Y (mm)', zaxis_title='Height (mm)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=700, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("형상을 렌더링할 수 없습니다. 물리적 변수를 다시 확인하십시오.")
