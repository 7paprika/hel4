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
    'd_o': 25.4, 't_thick': 2.11, 'D_c': 400.0, 'pitch': 31.75, 'D_s': 500.0,
    'shell_thick': 10.0,
    'D_mandrel': 350.0, 
    'tube_material': 'Stainless Steel 316 (k=16)', 'tube_k_wall': 16.0,
    'R_fi': 0.000176, 'R_fo': 0.000176,
    'overdesign_pct': 10.0,
    'design_p_shell': 10.0, 'allow_s_shell': 137.9, 'joint_e': 0.85, 'ca_shell': 3.0
}

for k, v in init_state.items():
    if k not in st.session_state:
        st.session_state[k] = v

def apply_json():
    try:
        parsed_data = json.loads(st.session_state['json_input_text'])
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
    st.text_area("JSON 로드:", value=json.dumps(init_state, indent=4), key='json_input_text', height=150)
    st.button("시나리오 적용 (Load)", on_click=apply_json, use_container_width=True)

st.subheader(f"🏷️ Equipment Tag: **{st.session_state['tag_no']}**")

# =========================================================
# [C] 1. 유체 식별 및 물성치
# =========================================================
st.subheader("1. 유체 식별 및 물성치")
st.radio("튜브 측 유체 상(Phase) 선택", ["Liquid (뉴턴 유체 - 물, 오일 등)", "Slurry (비뉴턴 유체 - 고농도 혼합물)"], key='fluid_type', horizontal=True)

col_tube, col_shell = st.columns(2)
with col_tube:
    st.markdown("#### **Tube-side (Inner)**")
    st.text_input("유체 명칭", key='tube_fluid_name')
    st.number_input("혼합 밀도 (kg/m³)", key='t_rho', help="일반 액체: 700 - 1000, 슬러리: 1100 - 1800 이상")
    st.number_input("비열 (J/kg·K)", key='t_cp', help="물: 4180, 일반 오일류: 1800 - 2400")
    st.number_input("열전도도 (W/m·K)", key='t_k', help="물: 0.6, 일반 오일류: 0.1 - 0.2")
    if "Liquid" in st.session_state['fluid_type']:
        st.number_input("동점성 계수 (cP)", format="%.2f", key='t_mu', help="물(20°C): 1.0 cP, 경질유: 2.0 - 10.0")
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
    op_mode = "🔥 Heater Mode (가열)"
else:
    est_T_cold_out = s_in + ((Q_kW * 3600.0) / (max(0.1, m_s) * s_cp_kJ))
    op_mode = "❄️ Cooler Mode (냉각)"

col_pc1, col_pc2, col_pc3, col_pc4 = st.columns(4)
with col_pc1:
    st.number_input("Tube 유량 (kg/h)", step=100.0, key='m_hot')
    st.number_input("Shell 유량 (kg/h)", step=100.0, key='m_cold')
    st.caption(f"💡 필요 쉘 유량 추정치: **{est_m_cold:,.0f} kg/h**")
with col_pc2:
    st.number_input("Tube 입구 온도 (°C)", key='T_hot_in')
    st.number_input("Tube 목표 출구 온도 (°C)", key='T_hot_out')
    st.caption(f"**운전 모드: {op_mode}** (Q: {Q_kW:,.1f} kW)")
with col_pc3:
    st.number_input("Shell 입구 온도 (°C)", key='T_cold_in')
    st.number_input("Shell 목표 출구 온도 (°C)", key='T_cold_out')
    st.caption(f"💡 예상 쉘 출구 온도: **{est_T_cold_out:,.1f} °C**")
with col_pc4:
    st.number_input("Tube 허용 ΔP (bar)", 0.1, 10.0, step=0.1, key='allowable_dp_tube', help="TEMA 가이드: 0.5 - 0.7 bar 권장")
    st.number_input("Shell 허용 ΔP (bar)", 0.1, 10.0, step=0.1, key='allowable_dp_shell', help="코일 외부 유동 특성상 0.3 - 0.5 bar 이내 설계 요망")

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
# [E] 3. 기하학 및 기계적 설계 (Clearance & Pitch 로직 보완)
# =========================================================
st.subheader("3. 기하학적 설계 및 기계 설계 (ASME Sec.VIII)")

col_g1, col_g2, col_g3, col_g4 = st.columns(4)

with col_g1:
    st.number_input("병렬 튜브 수 (N_p, 가닥)", 1, 50, step=1, key='N_p', help="유량을 N_p개로 분산시켜 튜브 내 유속과 ΔP를 낮춥니다.")
    
    do_options = {'3/8" (9.53 mm)': 9.53, '1/2" (12.7 mm)': 12.7, '3/4" (19.05 mm)': 19.05, '1" (25.4 mm)': 25.4, 'Custom (직접 입력)': -1}
    do_keys = list(do_options.keys())
    do_vals = list(do_options.values())
    curr_do = st.session_state.get('d_o', 25.4)
    try: do_idx = do_vals.index(curr_do)
    except ValueError: do_idx = len(do_keys) - 1

    selected_do = st.selectbox("튜브 외경 (OD)", do_keys, index=do_idx, help="표준: 19.05 mm (3/4\"), 슬러리/고점도: 25.4 mm (1\") 이상 권장")
    if "Custom" in selected_do:
        st.session_state['d_o'] = st.number_input("외경 직접 입력 (mm)", 5.0, 100.0, value=float(curr_do), step=0.1)
    else:
        st.session_state['d_o'] = do_options[selected_do]

    bwg_options = {'BWG 10 (3.40 mm)': 3.40, 'BWG 12 (2.77 mm)': 2.77, 'BWG 14 (2.11 mm)': 2.11, 'BWG 16 (1.65 mm)': 1.65, 'BWG 18 (1.24 mm)': 1.24, 'BWG 20 (0.89 mm)': 0.89, 'BWG 22 (0.71 mm)': 0.71, 'Custom (직접 입력)': -1}
    bwg_keys = list(bwg_options.keys())
    bwg_vals = list(bwg_options.values())
    curr_t = st.session_state.get('t_thick', 2.11)
    try: bwg_idx = bwg_vals.index(curr_t)
    except ValueError: bwg_idx = len(bwg_keys) - 1

    selected_bwg = st.selectbox("튜브 두께 (BWG)", bwg_keys, index=bwg_idx, help="일반적인 산업용 표준은 BWG 14 (2.11 mm) 또는 BWG 16 (1.65 mm) 입니다.")
    if "Custom" in selected_bwg:
        st.session_state['t_thick'] = st.number_input("두께 직접 입력 (mm)", 0.5, 10.0, value=float(curr_t), step=0.1)
    else:
        st.session_state['t_thick'] = bwg_options[selected_bwg]

    d_i = st.session_state['d_o'] - 2 * st.session_state['t_thick']
    if d_i <= 0:
        st.error("🚨 튜브 두께 에러")
    else:
        st.caption(f"✓ 유효 내경 (ID): **{d_i:.2f} mm**")

    mat_dict = {'Stainless Steel 316 (k=16)': 16.0, 'Titanium (k=22)': 22.0, 'Custom (직접 입력)': -1}
    mat_keys = list(mat_dict.keys())
    mat_vals = list(mat_dict.values())
    curr_k = st.session_state.get('tube_k_wall', 16.0)
    try: mat_idx = mat_vals.index(curr_k)
    except ValueError: mat_idx = len(mat_keys) - 1

    selected_mat = st.selectbox("튜브 재질", mat_keys, index=mat_idx)
    if "Custom" in selected_mat:
        st.session_state['tube_k_wall'] = st.number_input("열전도도 입력", value=float(curr_k))
    else:
        st.session_state['tube_k_wall'] = mat_dict[selected_mat]

with col_g2:
    st.number_input("코일 중심 직경 (D_c, mm)", step=10.0, key='D_c', help="파열 방지를 위해 외경의 최소 10배 이상 권장")
    st.caption(f"💡 추천 최소값: **{st.session_state['d_o'] * 10.0:.1f} mm**")
    
    st.number_input("Mandrel 외경 (D_m, mm)", step=5.0, key='D_mandrel', help="코일 내측 공간을 채우는 코어 기둥")
    
    # 🌟 내측 반경 클리어런스 (Inner Clearance) 실시간 계산
    inner_clearance_rad = ((st.session_state['D_c'] - st.session_state['d_o']) - st.session_state['D_mandrel']) / 2.0
    if inner_clearance_rad < 0:
        st.error(f"🚨 간섭 발생! 맨드릴이 코일을 파고듭니다 ({-inner_clearance_rad:.1f} mm 겹침)")
    else:
        st.caption(f"✓ 내측 틈새 (Radial Clearance): **{inner_clearance_rad:.1f} mm**")

with col_g3:
    # 🌟 최소 피치를 외경(d_o)으로 허용
    min_pitch = st.session_state['d_o']
    st.number_input("코일 피치 (p, mm)", min_value=float(min_pitch), step=1.0, key='pitch', help="튜브 중심 간 거리. p=OD일 경우 코일이 딱 붙습니다 (제작 가능하나 Shell 열전달 저하).")
    st.caption(f"💡 밀착 제작 최소값: **{min_pitch:.1f} mm** / TEMA 권장 여유: **{min_pitch*1.25:.1f} mm**")
    
    st.number_input("쉘 내경 (Shell ID, mm)", step=10.0, key='D_s', help="코일을 감싸는 압력 용기의 내부 직경")
    
    # 🌟 외측 반경 클리어런스 (Outer Clearance) 실시간 계산
    outer_clearance_rad = (st.session_state['D_s'] - (st.session_state['D_c'] + st.session_state['d_o'])) / 2.0
    if outer_clearance_rad < 0:
        st.error(f"🚨 간섭 발생! 코일이 쉘 벽면을 뚫고 나갑니다 ({-outer_clearance_rad:.1f} mm 겹침)")
    else:
        st.caption(f"✓ 외측 틈새 (Radial Clearance): **{outer_clearance_rad:.1f} mm**")
    
    st.markdown("#### ⚙️ 기계적 설계 (ASME Sec.VIII)")
    with st.expander("ASME 쉘 두께 설계 파라미터"):
        st.number_input("Shell 설계 압력 (bar)", step=1.0, key='design_p_shell', help="운전 압력의 110% 또는 운전 압력 + 1.5 bar")
        st.number_input("허용 응력 (S, MPa)", step=1.0, key='allow_s_shell', help="SA-516 기준 약 137.9 MPa")
        st.number_input("용접 효율 (E)", max_value=1.0, key='joint_e', help="RT 범위에 따라 결정 (1.0 또는 0.85)")
        st.number_input("부식 여유 (C.A., mm)", step=0.5, key='ca_shell', help="일반적인 부식 여유 (3.0 mm)")

    P_mpa = st.session_state['design_p_shell'] / 10.0
    R_mm = st.session_state['D_s'] / 2.0
    S_mpa = st.session_state['allow_s_shell']
    E_eff = st.session_state['joint_e']
    C_A = st.session_state['ca_shell']
    
    t_req = (P_mpa * R_mm) / (S_mpa * E_eff - 0.6 * P_mpa) + C_A
    t_final = max(6.0, np.ceil(t_req))
    st.session_state['shell_thick'] = t_final
    shell_od = st.session_state['D_s'] + 2.0 * t_final

with col_g4:
    st.number_input("Tube 오염계수 R_fi", 0.0, 0.02, format="%.6f", key='R_fi', help="튜브 내부 유체의 스케일 저항값")
    st.number_input("Shell 오염계수 R_fo", 0.0, 0.02, format="%.6f", key='R_fo', help="튜브 외부 스케일 저항값")
    
    st.number_input("여유율 (Overdesign, %)", 0.0, 100.0, step=1.0, key='overdesign_pct', help="계산된 필요 면적에 추가할 안전 여유율")
    
    with st.expander("💡 TEMA 오염계수(Fouling) 레퍼런스"):
        st.markdown("| 유체 | 오염계수 (m²·K/W) |\n|:---|:---|\n| 청정수 | 0.00018 |\n| 냉각수 | 0.00035 |\n| 공정 슬러리 | 0.00150+ |")

# =========================================================
# [F] 4. 수력학 코어 연산 
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

A_annulus = (np.pi / 4.0) * (D_s_m**2 - D_man_m**2)
A_free_flow = A_annulus * 0.5 
v_shell = m_cold_kg_s / (st.session_state['s_rho'] * A_free_flow) if A_free_flow > 0 else 0.0

D_e_shell = D_s_m - D_man_m
Re_shell = (st.session_state['s_rho'] * v_shell * D_e_shell) / max(1e-6, s_mu_pa)
Pr_shell = (st.session_state['s_cp'] * s_mu_pa) / max(1e-6, st.session_state['s_k'])
Nu_shell = 0.33 * (max(Re_shell, 1.0) ** 0.6) * (Pr_shell ** 0.33)
h_o = (Nu_shell * st.session_state['s_k']) / max(1e-6, d_o_m)

R_wall = (d_o_m * np.log(st.session_state['d_o'] / max(1e-6, d_i))) / (2.0 * max(1e-6, st.session_state['tube_k_wall'])) if d_i > 0 else 0
U_calc = 1.0 / ((1.0 / max(h_o, 0.1)) + st.session_state['R_fo'] + R_wall + st.session_state['R_fi'] * (st.session_state['d_o'] / max(1e-6, d_i)) + (st.session_state['d_o'] / max(1e-6, d_i)) * (1.0 / max(h_i, 0.1)))

Area_req = (Q_kW * 1000.0) / (U_calc * LMTD) if not lmtd_error else 0.0
Area_design = Area_req * (1.0 + st.session_state['overdesign_pct'] / 100.0)

N_p_val = max(1, st.session_state['N_p'])
p_m = st.session_state['pitch'] / 1000.0
D_c_m = st.session_state['D_c'] / 1000.0
Lead_m = p_m * N_p_val

Total_Tube_Length = Area_design / (np.pi * d_o_m) if d_o_m > 0 else 0.0
Length_per_Tube = Total_Tube_Length / N_p_val

Length_per_Turn = np.sqrt((np.pi * D_c_m)**2 + Lead_m**2) if D_c_m > 0 else 1.0
Turns_per_Tube = Length_per_Tube / Length_per_Turn

dp_tube_bar = (f_c * (Length_per_Tube / (max(1e-6, d_i) / 1000.0)) * (st.session_state['t_rho'] * (v_tube ** 2) / 2.0)) / 100000.0

L_shell_m = Turns_per_Tube * Lead_m
f_s = 0.316 / (max(Re_shell, 1.0)**0.25) 
dp_shell_bar = (f_s * (L_shell_m / max(1e-6, D_e_shell)) * (st.session_state['s_rho'] * (v_shell ** 2) / 2.0)) / 100000.0

# =========================================================
# [G] 실시간 Bounding Box 표시
# =========================================================
st.markdown("#### 📐 실시간 장비 예상 규격 (Estimated Bounding Box)")
Shell_TT_Length_m = L_shell_m + (2.0 * D_s_m) 
Shell_TT_Length_mm = Shell_TT_Length_m * 1000.0
shell_od_m = shell_od / 1000.0
Footprint_Area = (np.pi / 4.0) * (shell_od_m ** 2)

col_dim1, col_dim2, col_dim3, col_dim4 = st.columns(4)
col_dim1.metric("Shell 외경 (Shell OD)", f"{shell_od:,.1f} mm")
col_dim2.metric("코일부 순수 높이 (Coiled Section)", f"{L_shell_m:,.2f} m")
if Shell_TT_Length_m > 10.0:
    col_dim3.metric("🚨 Shell Length (T/T)", f"{Shell_TT_Length_mm:,.0f} mm", delta="과도한 길이! 배관/수리 불가", delta_color="inverse")
else:
    col_dim3.metric("Shell Length (T/T)", f"{Shell_TT_Length_mm:,.0f} mm", delta="안정적 구조", delta_color="normal")
col_dim4.metric("장비 바닥 면적 (Footprint)", f"{Footprint_Area:,.2f} m²")

st.markdown("---")

# =========================================================
# [H] 4. 상업용 데이터시트 및 PDF 내보내기
# =========================================================
st.subheader("4. 상업용 데이터시트 검증 (Datasheet & Report)")
st.caption(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
| Velocity (m/s) | {v_tube:.2f} (per tube) | {v_shell:.2f} (Annulus) | |
| Calc. Press. Drop (bar)| **{dp_tube_bar:.3f}** (Allow: {st.session_state['allowable_dp_tube']}) | **{dp_shell_bar:.3f}** (Allow: {st.session_state['allowable_dp_shell']}) | |
| **Mechanical Design** | | | |
| Tube OD x Thick. (mm) | {st.session_state['d_o']} x {st.session_state['t_thick']} | Tube Material | {st.session_state['tube_material']} |
| Shell OD x Thick. (mm) | **{shell_od:.1f} x {st.session_state['shell_thick']:.0f}** | Coil Pitch (Gap, mm) | {st.session_state['pitch']} |
| Coil Center Dia. (mm) | {st.session_state['D_c']} | Shell ID / Mandrel OD | {st.session_state['D_s']} mm / {st.session_state['D_mandrel']} mm |
| Parallel Coils (N_p) | **{st.session_state['N_p']} ea** | Turns per Tube | {Turns_per_Tube:,.1f} |
| Length per Tube (m) | {Length_per_Tube:,.1f} | **Shell T/T Length (mm)** | **{Shell_TT_Length_mm:,.0f} mm** |
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
        <tr><th>Tube OD x Thick.</th><td>{st.session_state['d_o']} mm x {st.session_state['t_thick']} mm</td><th>Tube Material</th><td>{st.session_state['tube_material']}</td></tr>
        <tr><th>Shell OD x Thick.</th><td>{shell_od:.1f} mm x {st.session_state['shell_thick']:.0f} mm</td><th>Shell Design Press.</th><td>{st.session_state['design_p_shell']} bar</td></tr>
        <tr><th>Coil Center Dia. (D_c)</th><td>{st.session_state['D_c']} mm</td><th>Shell ID / Mandrel OD</th><td>{st.session_state['D_s']} mm / {st.session_state['D_mandrel']} mm</td></tr>
        <tr><th>Parallel Coils (N_p)</th><td>{st.session_state['N_p']} ea</td><th>Coil Pitch (Gap)</th><td>{st.session_state['pitch']} mm</td></tr>
        <tr><th>Turns per Tube</th><td>{Turns_per_Tube:,.1f} turns</td><th>Length per Tube</th><td>{Length_per_Tube:,.1f} m</td></tr>
        <tr><th>Shell T/T Length</th><td colspan="3" style="font-size:16px;"><b>{Shell_TT_Length_mm:,.0f} mm</b></td></tr>
    </table>
</body>
</html>
"""

col_dl1, col_dl2 = st.columns([1, 2])
with col_dl1:
    st.download_button(
        label="📄 Datasheet 다운로드 (HTML/PDF용)",
        data=html_report,
        file_name=f"{st.session_state['tag_no']}_Datasheet.html",
        mime="text/html"
    )
with col_dl2:
    st.info("💡 파이썬 폰트 에러 없는 무결점 PDF 출력을 위해 HTML 파일로 내보냅니다. 브라우저 인쇄(Ctrl+P) 기능을 활용하세요.")

err_msg = []
if lmtd_error: err_msg.append("Temperature Cross (온도 역전) 발생")
if inner_clearance_rad < 0: err_msg.append("Mandrel - Coil 내측 간섭 발생")
if outer_clearance_rad < 0: err_msg.append("Shell - Coil 외측 간섭 발생")
if dp_tube_bar > st.session_state['allowable_dp_tube']: err_msg.append(f"Tube 측 ΔP 초과")
if dp_shell_bar > st.session_state['allowable_dp_shell']: err_msg.append(f"Shell 측 ΔP 초과")
if Shell_TT_Length_m > 10.0: err_msg.append(f"장비 총 길이 10m 초과 (레이아웃 한계)")
if d_i <= 0: err_msg.append("내경(ID) 계산 불가")

if err_msg:
    st.error("🚨 **Datasheet Warning:** " + " / ".join(err_msg))
else:
    st.success("✅ **Datasheet Validated:** 모든 공정 및 기계적 구조 제약 조건을 통과했습니다.")

# =========================================================
# [I] 5. 3D 형상 렌더링
# =========================================================
st.markdown("---")
st.subheader("5. 3D 코일 형상 (Schematic Representation)")

if Turns_per_Tube > 0 and Turns_per_Tube < 2000 and d_i > 0 and not lmtd_error:
    fig = go.Figure()
    
    t_max = Turns_per_Tube * 2 * np.pi
    t_base = np.linspace(0, t_max, int(max(Turns_per_Tube * 60, 150)))
    
    z = (Lead_m * 1000.0 / (2 * np.pi)) * t_base
    coil_height = max(z) if len(z) > 0 else 1.0
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    for i in range(int(N_p_val)):
        angle_offset = i * (2 * np.pi / N_p_val)
        x = (st.session_state['D_c'] / 2) * np.cos(t_base + angle_offset)
        y = (st.session_state['D_c'] / 2) * np.sin(t_base + angle_offset)
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode='lines',
            line=dict(color=colors[i % len(colors)], width=6),
            name=f'Coil {i+1}'
        ))
        
    z_surf = np.linspace(0, coil_height, 20)
    theta_surf = np.linspace(0, 2*np.pi, 25)
    theta_grid, z_grid = np.meshgrid(theta_surf, z_surf)
    
    x_man = (st.session_state['D_mandrel'] / 2) * np.cos(theta_grid)
    y_man = (st.session_state['D_mandrel'] / 2) * np.sin(theta_grid)
    fig.add_trace(go.Surface(x=x_man, y=y_man, z=z_grid, opacity=0.15, colorscale='Greys', showscale=False, name='Mandrel', hoverinfo='skip'))
    
    x_shell = (st.session_state['D_s'] / 2) * np.cos(theta_grid)
    y_shell = (st.session_state['D_s'] / 2) * np.sin(theta_grid)
    fig.add_trace(go.Surface(x=x_shell, y=y_shell, z=z_grid, opacity=0.08, colorscale='Blues', showscale=False, name='Shell', hoverinfo='skip'))
    
    noz_h = st.session_state['d_o'] * 3.0
    in_x = (st.session_state['D_c'] / 2) * np.cos(0)
    in_y = (st.session_state['D_c'] / 2) * np.sin(0)
    fig.add_trace(go.Scatter3d(x=[in_x, in_x], y=[in_y, in_y], z=[coil_height, coil_height + noz_h], mode='lines', line=dict(color='red', width=12), name='Tube Inlet'))
    
    out_x = (st.session_state['D_c'] / 2) * np.cos(t_max % (2 * np.pi))
    out_y = (st.session_state['D_c'] / 2) * np.sin(t_max % (2 * np.pi))
    fig.add_trace(go.Scatter3d(x=[out_x, out_x], y=[out_y, out_y], z=[0, -noz_h], mode='lines', line=dict(color='red', width=12), name='Tube Outlet'))
    
    sh_in_r = st.session_state['D_s'] / 2.0
    fig.add_trace(go.Scatter3d(x=[sh_in_r, sh_in_r + noz_h], y=[0, 0], z=[p_m*1000/2.0, p_m*1000/2.0], mode='lines', line=dict(color='blue', width=12), name='Shell Inlet'))
    fig.add_trace(go.Scatter3d(x=[-sh_in_r, -sh_in_r - noz_h], y=[0, 0], z=[coil_height - p_m*1000/2.0, coil_height - p_m*1000/2.0], mode='lines', line=dict(color='blue', width=12), name='Shell Outlet'))
    
    sup_lx = (st.session_state['D_mandrel'] / 2.0)
    sup_rx = (st.session_state['D_s'] / 2.0)
    supports_angles = [0, np.pi/2, np.pi, 3*np.pi/2]
    support_levels = [coil_height * 0.25, coil_height * 0.5, coil_height * 0.75]
    
    show_support_legend = True 
    for lvl in support_levels:
        for ang in supports_angles:
            fig.add_trace(go.Scatter3d(
                x=[sup_lx * np.cos(ang), sup_rx * np.cos(ang)], 
                y=[sup_lx * np.sin(ang), sup_rx * np.sin(ang)], 
                z=[lvl, lvl],
                mode='lines', line=dict(color='black', width=4), 
                name='Coil Support', hoverinfo='skip', 
                showlegend=show_support_legend
            ))
            show_support_legend = False

    fig.update_layout(scene=dict(xaxis_title='X (mm)', yaxis_title='Y (mm)', zaxis_title='Height (mm)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=700, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("형상을 렌더링할 수 없습니다. 온도 조건(Temperature Cross) 또는 물리적 변수를 다시 확인하십시오.")
