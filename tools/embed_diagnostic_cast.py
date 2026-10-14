#!/usr/bin/env python3
"""Deterministically embed diagnostic JSON and pinned Unicode upper mappings.

Normal compiler/CLI builds read the generated FREAK file only. Generation needs
Python's standard library, never a network, runtime JSON parser or subprocess.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src/diagnostics'
OUTPUT = DATA / 'embedded_cast.fk'
UNICODE_VERSION = '15.0.0'
# Pinned non-ASCII str.upper mappings, derived from Unicode 15.0.0. The
# compressed JSON is data, not executable input; its digest is checked below.
UNICODE_DATA = 'c-mE)%Tilwl7-*pjL*OzbQ|{ML{~>gPfkU2bX3&4U~w^52_%pKgTNRtV8B9PjD&ze8L%sSFb4bpX2_)K5qhtcYi%FT)`ygtYv-T)BK_iTf9omq{QArF;xB*y^>4ksnO}eT{r8Z4zy9)%{*c*3J`I^mWGQ4mkpm$Mi5v`BOym${=1C%lLnbBu@hoI-B1b|d)&4OW64k~+qS|;!RGSEiYLg*RtsD~7DwKVwHWd=prbD7yH6*IlLZaGCNK~5*iE8zbC@~ijCFUu!D6tR{C0>L?iD+LIC6+>>L?dKU;^H`Daugq;so5m&hv;N3N%kSymrF8yh@Rz=un*Cw9KxbIIfO+^@(7DQ<PjDJpGR06aUNlDn0bW7v0=GC#IY3+76(*7SR6$GVPU<1uocQ8!d62fY%L_hHbNq7GbF;cAu~@9wi6Ozdm)pszl1_mD<q;0DSHrg6f$Y#hjz$hfj*psOcv<FDP?c6Dj&{6CQEVgG-MKXF%U8dyBG?Ygk3xfnN<5{_kXA{o)=>w6O$JcA+c`dkcrESsgOzB1^b)9oL$U>L|8o}!sbFEY#}7V*xw9h=b{l3VJjgKwi*&)YatQF{$?;G7n>mw7X8JPTtt5{B^S|OOvy!)5>s*!4aSsQM1wIU7t!E6dJ+vTB(1!N1{cuEXfUSa_fSbwKSfh9B$uU-NwG_gZ>E?;T}FS4N!KrV8uvZHU#CMRb+3*>B8+|N>q+W<JPnzY__z`hB_#1)Hm9#QIiAb4kjZ;5Ux&mS*oHn_U@qT=golHW$x&Xuqr|dZ9*0cqTy{ey)vn%CVpXmNL-zfUNwTYFA@e_EQuvCa)0cblLna=sCPN}aB_uLLA99JED_)HH@(7y^iLmD(5jGzZVJ||WCFPJP%qi-_8GRLv!dhKLqi{xFMWe7-R~sP_#wqH<8GW@K5@FFkoY7Z%A(O)Y^?4#R4DW|5T4r%}Umb=-+;K>h>x9I6+2AbB>8rDlNx6^xA(OC=rI1P3$H9<E*hgLlvsmwsBOwts77}3-ArV#%i7=j~S)9@zt056K6B1$dkO-R#i7=j~S<J@A#gGVVgv5JSL*l*cY8L15$BmG9?`BAp*ba%XosbA)SF<>eKQ==mjOS(+OaJjCWRl@wKRSiAf7m|{oh-p8Ufr@-=1<WdEc2)650?2;^asoQDf)wD{uKSe>G`n#HgpDhH*_C#c*6Q$MirjIQ3cC?IT{kD8mr{6{FjxGNxI9akV&@3#+%THtA#A$&um8yvv4^RGJ`))hGyh;XcT`Q5>sCfS-?B?LKoqh%aX%Q;IXkA8derVvX$|6+y*X}LgEmXDKQ2Q`&`f*9w9C_LMEMhTpkLId|M&&D6=0LhZd<Z6rVV`IXoj=#v3pnm#vUVx=)cUi!feiayfP+-jU}4a0v?Vbj@?WfK&UA_$$`@k5<U!4S(<|TEOalISrW<`EnLAdG8laO|hpJ$v%&K=9(69jMu{<@!U5O5^ov}nS@@Cg-n*?di_Ue(#-4WkV!AEt07^w7BV@s>zR<rp<VN$Rzydx>mgC`c}P^83z_lZ7IC?~UI>Y5FGA-0fLg>Ub-ff4)fypDjq6#&MfiFpB&xj(iE6JxW`0OiTMLP5>mgBXBP6Q54vA`;AyJL<P{gWTZ-+#+Hz84NA|$GnL!w$G<d62@impEJIXnvE?yIA~vVVy%oa$fn-X!cxGzzEsm*@_MAzH!-hzvNRzpREtSR64<<1eh%^91MdmrZE|Zc8I_M;f7f(giP5qKocw&lB9ozqF+>x#!XuPeY=UWB>AA8Xh{K(X^W>>E!)4)6z-XZmQCWpPQO=lILbdI`MX+{J2Wq)TNXBH_t=k+2&?WI`MWhFO9l77WDe&g*56eN~7+QH0m~_QFmDybyuWOS3N1B?y5BEzLG}WHEGmcmquN!3s&ytwKVE#jj)V2Thgej^}?Foa0Yvlg-P^|H0th3qwbzG>b{jm-F|7*eJYK*C27<hkVf4>Y1ADGjTyKZmPXxY(x^Kkjk=@Ks5>T&y5rKQJ0Xp_lhUYLmPXx5Xgnu;U6D@me_fSMa(-QtPV#)+kWOO1Mn8M-u<&(T8nNmd9v8l<SGXvDZAv4y6&hF3uZPlzJ(5Q3u{2^k(unPb#`W;)nRF6+tN!B}b*rA>%5<wf;CghcW5-qKHqMtGTzhV-(ukdrMr>Ugv2)UhjhW}C|Jy}r#5SZ6tA1k6Z`DuC_O1GfdA?OYF~hg&C+7B6{lu)^s-Kw8+vsO6X7aWvjo6knVh^PednAq6=w~nH>b4_|*se5U&!m$%xr-U@#nZvvfOIm4cSF+2?A<++PUh`yR2s1{hx``fZc;j_d)F_W)V-UMPU_xOr4!G0Gt!CYyXZf^l(?IdM(lz#Vi%<m+mJ?V^q=20+^tF@c1;?w8`6l~ltygypI<KA?MNe5{l{G0ssEU(JM|xPb*KJguI|)-%+;OxkGZ;2|1np0>Obb{PW{JR-K$ratNW645_>-=oy6V`ODD1Saed%-4fkWxh@Fr|Y*`wy>Obb{KKjou9PVeN5nGo=?3^@W7o-sz{pZ&X_YG;pu1F(xRT{Bt(uj@zXK?+w-;_q|wlrdQq!Ana&!BJj`_jq0-M6HX^B^?tS@(z1$p20{nc@2*Y1Dczoy_z7u{7$orIXpd??|KWi8ShVrBU}ZH11jVXVR#9E}hi<)-RpZ{q|Hksr#)Yoz(p{Af43xHYlCc{Wc_>)crOroz(pn=U^Z1S>Hyale*tVrBQcG8g<8|QFlTbbtk1!w=9ji6=~F+l1ANl#^Co4->TB6Ta!lJ8EMp=l}6pVH2VB5qWdy%^u0AD$O5JXIe_1m2h;=wz>J^>h_3@O@b$e_7xVz03wi-_f(&3@KnDu~I(Q+VgGB)yED7kKA)te0eV0N9D*`%rDWHQ@0Uf*&(7~F34%P*9upyv>*8)1&6wtv|K!y&s1$6L6KnMELCqoCj0y@|e(1E@X%FsbmKnME*I%o;#K;Ino(ZQjB4&Djq;7C9R?*(*lETDt7fDSqW)`@SvGFjF+6R^&?zBxgiN>hM3m3;x~R9XVmsT>GUr*bI3kyhwB-^(Y-s&w8@(TOhj$u`d`YCOT_Gf&bd*gUVUsqXcYXP#Huul_qe#n1C}&1Z4!k4vWleqw(WfX`Wv%e)HYbGW*FKkgUc2#-qw9Mtik0LO9c7&PyAB%sIyV*)0a5HLYmzywnQCWubtpD@9UfC=gXCYTd2!GeGZ76W*G9ybI`up(fBRRI&M37B9bfT!2-rho~y1x&CbV1hjX6Ep*Ob{w|^OmHY*f+GPF91EDB6Tsm<?h2UTOn?OKegP7+O9CWl$NJ<swe4X660}DIOfV*3f(Zc=#QNlOOfV&20<BMu3A8>rCeZrim_X~3X9BHHo(Z%*c_z^M<e5P0lV<|04=1s$_2DG8wLYB0w$_J}*w*@R65CoIPGVc@!%1vweK?72tq&)$t@Ys~wqtz?oW%CAfC)MRCg=*7;7ou7omig&C$Uo!AVFtPfCQak0TOgZ1WXX?Q{W_aCIn1S7BIn-fC;JsCW!SZ;G+GXpZ5hxw!eN>9bB~k_p|C?M*lB`<g)P}|J3ntV6{F4j%CL{JF5cPSrgFChJbcru?if^&bELFb_7hYCt!l6fC*x;3LMMMp@0drSRBia7K>xq(PD8dJ6bG`Wk(0cu{_aYaV$@?SRBg}Ef&Y}M2p3-JW&%lmM7{P$MQsr#j!lmVsR`_v{)R=6D=0U@<fZpu{@~@m|#x81aUGIIhH4j0w!n(m|#V~1gioji1jIQEKfEBOt2|nf^7j4><E}3)~Cp^JZTD;pe0~}Lje;U378<(r^pNBNk_m0T>%rE32^J|jtG#gJ1W3KLU&An)ZOs_J|uJ}1gO)U6yWCFEelYzTM5YWl{o=lnHS);-c{o{qumz*debU!V7p5JIeJq^Iegu%fIPjay`04E8vz}t*Bs04u7D2Ic+P0|Z9svqsG}UdZd*WaYA+|Tdm^AW^_pYZjYooFk>1pJ&S;kpJ%uND?D&2<BET!BqXM`-9TULy>9_#iPA3HLb~+h=$D!->&ovRuoz4pi@zUphG5npr2*3j{UwkU2ktIQIy!b~+OfSm;d^|nf6!4WT0bOnj=<<yK9X#C;(B!TF9X#C=(BazveCz)GtRuiHXD0!CpgdOxc?~>Q2RV7?>L4fYTpi@(oi7OB?OdJU<eeW2;O)FEfP-@#53if&I-VRI$Qv)B=kk{06pd(`;|VXL-O&^|Nn<H;mc~=$G)<()d73oFw3k!lOjT0s{i$xud|EfAKCK&bpVrOieyYoh^`Gh%ey&^mscwO;HdCaltrY2MJ4L#BlOkR1q)1o0Dbm$migfih#lp{Zi$B$kvoEb1=U-a4*!xr6V&<p1#lD~F7PCLqEpn36y1cEN{;11o{!y3n?7BU1=I^A)Q*Jj!o>zM*^2~ahV&9+Z_QW+{E5+QO>+<{TKi4h%T(|gBU49t<QI~hKA9eW=?d(_pPiJjGAJ5P9jod{`374helyD`Q*42dHZiD<PK3D&U#Aj)1envhYOOe}bDRFNvB_w(761ez){3>?`(@1`ZJ)aZsTHsf5+EnZp=l{IPm^@}8&%CQ}+b?<599M-+0j~;Mf?n-7Dla$d)_>&Xj@?UL#rf6v_wyYAFYsxJd<2?#a-OG)kmnYj3Fqc@B_(*+av)AcQ2J`&Pmx(H!oy%}%4Ts`4?`=09>7Zh_T7h81=x5WdL_Wl`_P&IyVXPM0;C?=5MY;j=(V5#*c9L+^-#1go2P?q0Uf*%(7}#?4t51}uqU8{xUpo>mWSa1Z4l#a)guAkR(&sk(dw}PMyqWBj8;1W7_FXYj~S_}T>*?%PX#bqJrlra^;`f4wSEB{)U+>+yXHf!B!GjOT;s0!P#YA$L2XD|+i+0RMmV0=9%|17a8T2}IG)!YYT6m^qXX}a)4{la4kiS2Fe#vevVaaM-gH8tX1@uQnomtA)hwA%t2tmovF4x&)tW;llxq%~P_L;CIDVJ+&>S)0n46;}dKoj(%eaYNCQS4)X`+|1iC%nsT>j>iiC(6?$wn_#6TQ?-^fF_jmsu0N)J^pA+(a*PCVH7S(aVB~US5be3e80my)2pNrD39%WfQ%unCRuDiC$Js^zzC?FKZ@xS@(t`y=<81<+X`kyk(iCmn{>$cndR2FK<lrl5T0z%dUxDyv3QN7i|dh2Zs;)K0aKWK6VUA%8zFT<k+`MUW4}Si`SifJIV9=KW&_H7vo|7owrnRJT0FMc$#=<dH(VA@X+$a<7wfcr5Wcw!9#1r#4KYbW|=TCOWDLMQ{Kd7ma2(aW=zadH!;hciCHvP{B7bxYth6k4HL7hn3!eN#4KyxL}r!^6SHiZm}T3<EITG<(OSket<^L!i?^&ft1WL@b2?kzw&pyxym8G5Y<cUNGuP^xnB~lbEC>B2WI53K^>LC822IFv;PvB8@4)NF8{L7|k2kjiuODw{2VOtk#16cEym1|P{qoG>_2bkXc>M~@;`J*qi`TEfEMC6?vv~aq%;NPcGK<zPiwD++gEuD3^}()*S=9L~_ftwMCOrF;UYhU-S#nN(mMpz8;Zdx#X2OF{Y2Ac}+R}yz&$Ol2COr3)Hcfb<Ep7P+2lTRSq8A?nKfIQ9O!VR-;>Xw0o{3)Gn&_ozqL+OWy|@$n3|l%7@#~Y)p^0AJnds%nL@)16^m1&Xm$r#sIwpEKG0}^EhQUwGrBe|<HkbUf41R7dotxlgpx*>915ZuxGEg$X%fNsMUIqqD@G>xDLiGXNrTGx}eIR~2+{?$v$N7E}ek(a&GGS|Fe$a%UCe9C=@YBNi5mCM;-H`z?%Y=zp$|h!+GBHb4RA81F6SLG!%ra+UmIV{DEQ*TE(l9a0iiufPP0X@pVwTuD?By>{ALlns%(87_mK_n!mB)pC6LKz;Ovt&Q4(4zMJT45IkaJ<g#4KYbW|=TCi#nL=W0olsvs6vYGGk(vx`|oTLH>61aX}sAX2av+stNC0RA0E=@VK~PLcPUJ6Y4E)o0w(C#4NE#+RJT*$HkV3afc?x9hn$+Eb3wPj)_^iCT2M^A<I&~30ao34%}~eTpBbX%hIrk8;Bz&W*IXvi`Ier43A4?6SGX2n5AlBmKhVXXdSrO@VGQ*VwMFHvn-mJrD0+gO)_^J9+y^4%(7-;mJJiLY?_!wE5>by$E6(;vv|eux$SYOZNg^i(us*#+<Bh24R@aBZNr`CdE0R3IcE)b9$)`FHpWeS&Hd!`G}O-`?thQVgC<s}n^<Aa#4HOYW>G)6Kk(RSn3!e7#4M{OW?3^ai~7k;g2#sX$uIdI8;2%lIWjTJv58qU$@~WYvC%a#%b5vTmitY}vaEjcEB(jiXC|!C@~DWbxjbcJoV&#9^|HH!ug4yj^&^9riH84;g<t5ES4_Bfl=YL00>92HubOb@D!($}&Q)GB;m%cFH{s4z-Z0?~RDNy3ovXZQ!kw$UWuljD6TRri8Jvml<sB2f?3(Ch&qOb8P4v<<(aXMxURox4IWW=7p^0A9!6Lu9D<7HY<-Lhsj!pE^HqlGRL@y^Mdg+?z<<vwkXC`_%7x4+O(r<#7%2N}6=TS28haLka{?cR6#GiT$nfP0eVH1Ds@yrA-l@SxXR7OR70<4Ug=w;kQFB2wunKaQ$*+efD6TM8C=w;eOFI5x0=toeofmWF@(aWrfUg{=#d2XVYITO9io9Jc1L@zH)^s;E87yTTH|FZDC(lF7>vWZ?+O!V^7L@%o*dU<7{mo*c;tefa%!$dDS|M(9L-z%FYdf773%eIMLeExBRrQ-9CPn8v)f81WF`26GUO69Ho?*%@8`^}KN^xIzyiOb*q+fc;Y{1Qz5mc9m)zyH<H`zOG|=C{H4=^v244~$<m0`tTZBYv${{_*A_Up<ZgqT%-~|LVRp<v^>ZJm{6F09rE@LF*!{^uM|rrXJ91Q!i-KlmTs-`as(zdU<1_mmL$m?3(Ch&qOb8MLBwDn&@TUL@zB9y&Rb6<<LYg?@aV^WTKb%CVDwG(MwyDr<YFrn^F$f@_$cF^&5MLPmR6Ak}*RZF!m7#jalN5F-IIW=84aY1>%UYNE{XRgsU-QxEeQxs|jPcnly&1vN2p$jNxj^7_O#`;i_s3S2ba8xSBDBt65{XsvE=Ab7Q!gGlr{qW4Kx{hN~CGaJ6U*S4+Z7xM~=~)v_^Mtr)}AOJlfNHHNEK#&ES}3|H&MaJ69!S8;~r@_EKqn?}Y~_l=CLwv3Fe9taCOqUxcMM^t@h<PpVw1&~KneQ)Fu#hwL_M-;mjz;M+uhN}}}xau0i)v2%;uFj0%>fA_IwSFUA)t(yZs#Y@6Rc*jXSG7SSUDbw+bX6NR(p638Q6bLX+K7>^YNN(*HD(M~<Hm3`VGLK3#&A_OhO3G(Tum9nmCmC=oWHfIF<j|9;$7+AQ?pGYQ_b!hnQB(E!C$x}cwl6z*+U}_aQ2;%2RM6V<N?n5Uo!JNz}aIX4{)|^3|Adv*w8Q(V<u-$jbY==7&gw0v{COj(nkHMkv8fjBW=_NjI>c7G_pDMAtPPYH4Md=$@()RUDZd7bX6ZUhO04S*qAVejY(tJC>z5@#TYiG^#83fg!O4-*r*z#?u;?I5tq$^1~_&HfQ)TDHS!Q*w*bggtpOub#qI%+N7NcJ@`z$L0mvh2Ju~u%Vs`<^BWjHbV}N6~0T`~vjp1s-7_KIb;i_y5R~2Kpnlgr~X=Avm8pBmh7&oBUy#R(QcQS53v6}%5SI>>%YR(w0=8fTM!5FSy7{k?~F<dPP;|3JFA;568Yz$W`#&Gr07_L^0;p&w!T&)?y)w(fUZ5YGVYhhow+BAl%En~RaHioM=#&ES`3|G6xaJ6R)S8t8ss%Z>Y`@(Fvir+T&6nOcXUR^O}h%b$O#8qRK_{x|gt{L;hbz_0JVJs3~3wbr0UfneI5VwrsYTFpD-WbExjxk*A8pG9|F<iYhhO4GAT<r^s;mXY^hN}Z(xH>e3t9Qn5bz}@z?~UQ=*ch(b#&Fd!hO78}V-LUWNU&=RSEt5sb!H4#@w<jhJQdXA$MwJr@u{(oSTbgb1I8S2(3mF<84JW=W04rYbI8O+wH`mv2lfz0jp1s{7_P>R;cCJdt|pD)s%#8b6=S%XGKQ;ZVNbZK8pBo17_MfF;cC_xuIk2c_1qY)=8WNL-WaYHjN$5qus2*S8pG9+F<do_;c8j`jLCmR{dZ%nKjk9%shP<eYo(NX$O9?&k_S`HkcU$4BM+yXB|l3!M;=KzPaaJ<{Eej?{>IIj@Hdfi_?t{Q{FPG<f0dNO-&D%sZ#w1hS4}zm)lv?BGbx9^S#w|btEU|Po~IoC=28xS^C^eFg_OhJi<HCPV#?ufDdq6jNICqa>z@sOD=CM+<O=@x{|6DvGBW'
UNICODE_SHA256 = 'ea4e5f56df8bf07479975ca293322e4cafe6426212f8b2e753e903cefaf88183'


def literal(value: str) -> str:
    if '\0' in value:
        raise ValueError('embedded FREAK literals cannot contain NUL')
    if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
        raise ValueError('embedded diagnostic text contains an unsupported control character')
    return json.dumps(value, ensure_ascii=False)


def read(name: str):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def lines(value, label):
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        raise ValueError(f'{label} must be a nonempty list of nonempty strings')
    for item in value:
        literal(item)
    return value


def index_function(name, values):
    body = [f'task {name}(index: int) -> word {{']
    body += [f'    if index == {i} {{ give back {literal(value)} }}' for i, value in enumerate(values)]
    body += ['    panic("diagnostic cast: invalid embedded index")', '    give back ""', '}', '']
    return body


def generate():
    paths = [DATA/'codes.json', DATA/'easter_eggs.json', DATA/'resources.json', *sorted((DATA/'packs').glob('*.json'))]
    fingerprints = '\n'.join(f'{p.relative_to(DATA)} {hashlib.sha256(p.read_bytes()).hexdigest()}' for p in paths)
    fingerprint = hashlib.sha256(fingerprints.encode()).hexdigest()
    output = ['-- Generated by tools/embed_diagnostic_cast.py. Do not edit.',
              f'-- Diagnostic JSON inventory SHA-256: {fingerprint}',
              f'-- Unicode uppercase mapping: {UNICODE_VERSION} SHA-256 {UNICODE_SHA256}', '']
    raw = zlib.decompress(base64.b85decode(UNICODE_DATA))
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != UNICODE_SHA256:
        raise ValueError('pinned Unicode mapping failed integrity check')
    mappings = json.loads(raw)
    offsets = ''; values = ''
    for point, upper in mappings:
        # Each ASCII record is decimal codepoint(7), UTF-8 byte offset(6),
        # byte length(2). Fixed record width allows bounded binary search.
        offsets += f'{point:07d}{len(values.encode("utf-8")):06d}{len(upper.encode("utf-8")):02d}'
        values += upper
    output += [f'task diagnostic_cast_upper_rows() -> word {{ give back {literal(offsets)} }}',
               f'task diagnostic_cast_upper_values() -> word {{ give back {literal(values)} }}',
               f'task diagnostic_cast_upper_count() -> int {{ give back {len(mappings)} }}', '']
    packs = []
    for path in sorted((DATA/'packs').glob('*.json')):
        pack = json.loads(path.read_text(encoding='utf-8'))
        speaker = pack['speaker']
        if speaker != path.stem.upper():
            raise ValueError(f'{path}: speaker must match filename')
        top = lines(pack['lines'], speaker)
        subsets = {k.lower(): lines(v, f'{speaker}/{k}') for k, v in sorted(pack.get('platforms', {}).items())}
        packs.append((speaker, top, subsets))
        output += index_function('diagnostic_cast_pack_'+path.stem, top)
        for platform, subset in subsets.items():
            if not platform.isascii() or not platform.isalpha():
                raise ValueError('platform labels must be ASCII letters')
            output += index_function('diagnostic_cast_pack_'+path.stem+'_'+platform, subset)
    if len(packs) != 9 or sum(len(p[1]) for p in packs) != 103:
        raise ValueError('expected nine canonical packs and 103 top-level lines')
    output += ['task diagnostic_cast_embedded_count(speaker: word, platform: word) -> int {']
    for speaker, top, subsets in packs:
        condition = f'speaker == {literal(speaker)}'
        if speaker == 'FREAK':
            condition = '('+condition+' or speaker == "")'
        for platform, subset in subsets.items():
            output += [f'    if {condition} and platform == {literal(platform)} {{ give back {len(subset)} }}']
        output += [f'    if {condition} {{ give back {len(top)} }}']
    fallback = next(len(p[1]) for p in packs if p[0] == 'FREAK')
    output += [f'    give back {fallback}', '}', '', 'task diagnostic_cast_embedded_line(speaker: word, platform: word, index: int) -> word {']
    for speaker, top, subsets in packs:
        condition = f'speaker == {literal(speaker)}'
        if speaker == 'FREAK':
            condition = '('+condition+' or speaker == "")'
        for platform in subsets:
            output += [f'    if {condition} and platform == {literal(platform)} {{ give back diagnostic_cast_pack_{speaker.lower()}_{platform}(index) }}']
        output += [f'    if {condition} {{ give back diagnostic_cast_pack_{speaker.lower()}(index) }}']
    output += ['    give back diagnostic_cast_pack_freak(index)', '}', '']
    resources = lines(read('resources.json')['lines'], 'resources')
    output += [f'task diagnostic_cast_resource_count() -> int {{ give back {len(resources)} }}', '']
    output += index_function('diagnostic_cast_resource_line', resources)
    output += ['task diagnostic_cast_embedded_egg(source: word, code: word) -> word {']
    for egg in read('easter_eggs.json')['eggs']:
        condition = f'source == {literal(egg["exact_source"])}'
        if egg['code'] is not None:
            condition += f' and code == {literal(egg["code"].upper())}'
        output += [f'    if {condition} {{ give back {literal(egg["line"])} }}']
    output += ['    give back ""', '}', '', 'task cli_diagnostic_cast_code_known(code: word) -> bool {',
               '    pilot upper = cli_diagnostic_cast_upper(code)']
    codes = read('codes.json')['codes']
    if [c['code'] for c in codes] != [f'E{i:04d}' for i in range(1, 11)]:
        raise ValueError('stable diagnostic code inventory changed')
    for code in codes:
        output += [f'    if upper == {literal(code["code"])} {{ give back true }}']
    output += ['    give back false', '}', '', 'task cli_diagnostic_cast_default_speaker(code: word) -> word {',
               '    pilot upper = cli_diagnostic_cast_upper(code)']
    for code in codes:
        output += [f'    if upper == {literal(code["code"])} {{ give back {literal(code["default_speaker"])} }}']
    output += ['    give back "FREAK"', '}', '']
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    generated = generate()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != generated:
            raise SystemExit('diagnostic cast generated source is stale; run tools/embed_diagnostic_cast.py')
        print('diagnostic cast embedding is current')
    else:
        OUTPUT.write_text(generated, encoding='utf-8')


if __name__ == '__main__':
    main()
