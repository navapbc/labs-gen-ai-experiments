from llm import google_gemini_client, ollama_client, gpt3_5, gpt_4_turbo;
from langchain_core.prompts import PromptTemplate

transcript = """
1046

02:06:30.300 --> 02:06:33.410

Rebecca Hale: thank you for calling benefilli. This is Rebecca. Happy to help you.

 

1047

02:06:33.770 --> 02:06:39.719

James Joyce: Yeah, I was just

 

1048

02:06:40.240 --> 02:06:43.280

James Joyce: hunting around and

 

1049

02:06:43.930 --> 02:06:47.020

James Joyce: I got your number.

 

1050

02:06:48.830 --> 02:06:50.130

James Joyce: because.

 

1051

02:06:50.700 --> 02:06:52.260

James Joyce: well, so like.

 

1052

02:06:53.070 --> 02:06:56.030

James Joyce: so, yeah, I need some help paying for rent.

 

1053

02:06:56.420 --> 02:06:58.710

Rebecca Hale: And

 

1054

02:06:58.850 --> 02:07:06.919

James Joyce: yeah, it was like you were the place that everyone I like talked to like 2 or 3 different places. And they said, A call, you guys, because you guys do rent assistance.

 

1055

02:07:08.510 --> 02:07:14.340

Rebecca Hale: I could definitely provide you with some information what is your first and last name.

 

1056

02:07:15.380 --> 02:07:16.660

James Joyce: James.

 

1057

02:07:20.120 --> 02:07:21.520

James Joyce: joyce.

 

1058

02:07:21.670 --> 02:07:26.820

Rebecca Hale:  JOYC. E.

 

1059

02:07:38.560 --> 02:07:39.730

Rebecca Hale: Okay.

 

1060

02:07:47.110 --> 02:07:54.940

Rebecca Hale: thank you so much for calling us today, Mr. Joyce, what is a telephone to reach you in case you get disconnected?

 

1061

02:07:55.210 --> 02:07:57.370

James Joyce: 2, 3, 4,

 

1062

02:07:58.680 --> 02:08:00.279

James Joyce: 5, 6, 7,

 

1063

02:08:01.790 --> 02:08:03.880

James Joyce: 8, 9, 0 1.

 

1064

02:08:06.140 --> 02:08:08.050

Rebecca Hale: And what is your Zip code?

 

1065

02:08:08.200 --> 02:08:11.249

James Joyce: 1, 9, one.

 

1066

02:08:12.240 --> 02:08:13.440

James Joyce: 2, 6,

 

1067

02:08:17.090 --> 02:08:18.160

Rebecca Hale: alright.

 

1068

02:08:18.330 --> 02:08:27.860

Rebecca Hale: So while I am setting up a portfolio for you. Let me just explain who we are and what we do here at Ben Affili we are partnered with the State

 

1069

02:08:27.960 --> 02:08:29.570

Rebecca Hale: to complete

 

1070

02:08:29.610 --> 02:08:43.440

Rebecca Hale: complete screenings and help people apply for benefits such as snap as well as medicaid and some other benefits. And is that how? I can get the money for the rent

 

1071

02:08:43.920 --> 02:08:54.350

James Joyce: cause that I mean, it's gonna be, I mean, I'm like a month behind. And my landlord's kind of annoyed. So

 

1072

02:08:54.450 --> 02:09:06.910

Rebecca Hale: so this is this is how I get the money for rent is you're gonna ask me some questions. So unfortunately, we cannot. We don't have any programs that specifically apply people for rental assistance.

 

1073

02:09:06.910 --> 02:09:29.289

Rebecca Hale: What I could do is I could take you through a screening for other benefits that might be able to provide you with some additional money each month that you could then like offset the cost of your rent. So, for instance, if I helped you apply so like my rent is gonna be like $1,000. So you can help me get a benefit that will like save me 1,000. So I can give it to my landlord.

 

1074

02:09:29.660 --> 02:09:44.810

Rebecca Hale: I don't know if we'll be able to save you specifically 1,000. But, for instance, if we apply you for like something like if you're likely eligible for snap, which is the food stamps? Oh, yeah, no, no, I mean, I already get Snap, but it's like 20 bucks. Can you give me more of that?

 

1075

02:09:45.190 --> 02:10:11.679

Rebecca Hale: So I can't help you. If you're already enrolled, I wouldn't be able to assist you with getting more benefits. Although I do encourage you to make sure that you have all of your expenses updated with your snap case to make sure that they're really factoring in your benefit amount? So, for instance, making sure that they do know how much you pay for your rent as well as well, I mean they they know how much I'm supposed to pay for my rent like I haven't paid it. I didn't tell. Should I tell them I haven't paid it.

 

1076

02:10:12.310 --> 02:10:33.280

Rebecca Hale: If you're if you're obligated to pay that, it still counts as an expense. Yeah. So if they know that you're you're responsible for paying 1,000 a month for rent. That's the most important thing that they have on file. Same thing with, like they'll they'll provide you with, like, you know, your full utility amount? If you're disabled, you can report any medical expenses.

 

1077

02:10:33.720 --> 02:10:35.749

Rebecca Hale: And such

 

1078

02:10:35.820 --> 02:10:57.569

Rebecca Hale: are you currently in, do you guys? So you guys don't do rental assistance. We do not have any programs that assist with rental assistance. Specifically. There is a program called the Property Tax and Rent rebate for either seniors or people with disabilities. That you may qualify for. Are you familiar with that program?

 

1079

02:10:57.610 --> 02:11:06.429

James Joyce:  no, I don't think I would qualify. I don't think I have a disability or anything.

 

1080

02:11:06.530 --> 02:11:23.690

Rebecca Hale: I can provide you with some referrals for other agencies that do more direct support with with rental assistance. Are you receiving assistance? Did you apply for Lie heap this year?

 

1081

02:11:24.520 --> 02:11:45.629

Rebecca Hale: You could still, qualify for why he and what it could do is, it could provide like as long as there's not a specific like if there's a specific amount, that's all wanted to rent you could still apply for energy assistance. He's kind of annoyed with me right now. I don't really wanna like

 

1082

02:11:45.840 --> 02:11:48.880

James Joyce: take anything to him. Would I be able to get it without like.

 

1083

02:11:48.900 --> 02:11:55.900

Rebecca Hale: if you provide a copy of your lease and that like states that utilities are included with rent.

 

1084

02:11:56.020 --> 02:11:57.730

Rebecca Hale: that would be able to suffice.

 

1085

02:11:58.500 --> 02:12:07.439

James Joyce: Yeah, I mean, I've been at this place for a while. I mean, I might have, though I haven't gotten a new lease. It's probably like 3 years old, like, can I still use that?

 

1086

02:12:08.400 --> 02:12:14.750

Rebecca Hale: Yeah, that should be fine. If that's the most current lease that you have like, if it doesn't have a specific expiration date

 

1087

02:12:14.900 --> 02:12:15.670

Rebecca Hale: for that.

 

1088

02:12:16.440 --> 02:12:17.260

James Joyce: Okay.

 

1089

02:12:17.640 --> 02:12:30.830

Rebecca Hale: okay. so would you want to do an application for lie heap today? I'm yeah, I mean, sure. Alright. And you are in Philadelphia County. Is that correct?

 

1090

02:12:31.280 --> 02:12:32.759

Rebecca Hale: What is your address?

 

1091

02:12:32.920 --> 02:12:35.190

James Joyce: 1 21

 

1092

02:12:35.760 --> 02:12:37.590

Rebecca Hale: street

 

1093

02:12:39.800 --> 02:12:43.360

James Joyce: Philadelphia. PA.

 

1094

02:12:44.170 --> 02:12:46.839

Rebecca Hale: So it's 1 21 street

 

1095

02:12:58.370 --> 02:13:10.019

Rebecca Hale: alright. And before we get started. I just have to ask you this permission question. Do I have your permission to collect information about you and your household to determine whether you're likely eligible for public benefits, and to help you apply

 

1096

02:13:10.980 --> 02:13:15.569

James Joyce: well, so like when you say household so like

 

1097

02:13:16.610 --> 02:13:20.640

James Joyce: I mean, like I live in a house like. And I'm renting a room.

 

1098

02:13:20.970 --> 02:13:22.510

Rebecca Hale: Okay? So like.

 

1099

02:13:24.380 --> 02:13:25.450

James Joyce: so

 

1100

02:13:25.850 --> 02:13:30.980

James Joyce: is that like, my, is it like my household is like the people I'm living with.

 

1101

02:13:31.310 --> 02:13:58.670

Rebecca Hale: like cause I have. I like II mean, I just have my own room. It's got like a little kitchen Ed in it, and it's got all of that. So like it's my own like, but I still have to like walk through the rest of the house, and like we share like a bathroom cause I don't. I don't have my own bathroom, but like, okay, and is so, do you have a separate line for your heat like, or is it all just like the entire household shares the same kind of heat that is covered by your landlord.

 

1102

02:13:58.810 --> 02:14:00.939

James Joyce: I mean, I have like event.

 

1103

02:14:01.340 --> 02:14:09.090

James Joyce: end of my room. Oh, I wish I wish I had thermostat.

 

1104

02:14:09.280 --> 02:14:25.589

Rebecca Hale: Okay. In that case, for the energy systems benefit, it would have to include everyone who lives under the same house. So if you're like renting a room. But then there's other individuals within that house we would have to include their information as well.

 

1105

02:14:26.870 --> 02:14:35.279

James Joyce: I don't. Yeah, I'm I don't think that's gonna work. I'm not. We're not. We're not in a great place right now.

 

1106

02:14:35.400 --> 02:14:40.689

James Joyce: Okay. I'm sorry to hear about that. I mean it. Yeah, I don't know. It is what it is.

 

1107

02:14:40.800 --> 02:14:52.000

Rebecca Hale: Okay. Alright, but in terms of other benefits. Would you? Do you agree to the permission statement to see what all other benefits you may qualify for. Oh, I'm sorry. What? What was the permission statement?

 

1108

02:14:52.210 --> 02:15:06.790

Rebecca Hale: Do I have your permission to collect information about you and your household, determine whether you're likely eligible for public benefits and to help you apply

 

1109

02:15:07.320 --> 02:15:28.229

James Joyce: like I'm not gonna be able to give you anything like my landlord, or like his kids like I don't really have anything to do is we could just screen you for the benefits that only look at one applicant so that we wouldn't have to necessarily include your other household members.

 

1110

02:15:30.480 --> 02:15:32.530

Rebecca Hale: Alright. And how old are you?

 

1111

02:15:32.780 --> 02:15:34.810

James Joyce: I'm 36.

 

1112

02:15:43.470 --> 02:15:47.849

Rebecca Hale: Just give me 1 s. I'm closing out the benefits that relate to seniors.

 

1113

02:15:55.670 --> 02:16:00.219

Rebecca Hale: Now, I know you said you're currently receiving food stamps. Is that correct?

 

1114

02:16:01.150 --> 02:16:02.710

James Joyce: I think it's like 20 bucks

 

1115

02:16:03.070 --> 02:16:04.410

Rebecca Hale: Umhm capture.

 

1116

02:16:06.270 --> 02:16:10.309

James Joyce: So yeah, if I mean, if there's a way you can give me more of that like that'd be cool.

 

1117

02:16:10.870 --> 02:16:22.889

Rebecca Hale: Unfortunately, I wouldn't be able to add any additional benefits on your case, but I do definitely encourage you to make sure that they have your most updated expenses and income information cause. That's how they calculate the benefit amount.

 

1118

02:16:24.410 --> 02:16:27.559

Rebecca Hale: Now, are you currently enrolled in Medicaid?

 

1119

02:16:27.720 --> 02:16:29.910

James Joyce: Well.

 

1120

02:16:33.100 --> 02:16:37.869

Rebecca Hale: no, I don't think so I don't think no, I don't have any health insurance right now.

 

1121

02:16:39.360 --> 02:16:43.289

Rebecca Hale: cause that is something that we could screen you for as well.

 

1122

02:16:44.809 --> 02:16:51.929

Rebecca Hale: I do have a tooth that's bothering me right now. Oh, I'm sorry to hear that I can give you a referral for a dentist, if that is helpful.

 

1123

02:16:52.840 --> 02:16:57.540

James Joyce: Maybe I don't really like the dentist, but I mean, I guess it's worth having.

 

1124

02:16:58.690 --> 02:17:00.680

Rebecca Hale: Yeah, you gotta take care of your sheets, right?

 

1125

02:17:02.200 --> 02:17:05.569

Rebecca Hale: So my mom always tells me

 

1126

02:17:06.370 --> 02:17:08.209

Rebecca Hale: so does mine

 

1127

02:17:09.340 --> 02:17:10.490

Rebecca Hale: alright.

 

1128

02:17:26.969 --> 02:17:33.650

Rebecca Hale:  Didn't close any of the benefits let me just close for.

 

1129

02:17:41.430 --> 02:17:44.339

Rebecca Hale: And you said that you don't currently have a disability. Is that correct?

 

1130

02:17:44.570 --> 02:17:45.910

James Joyce: I mean.

 

1131

02:17:46.120 --> 02:17:48.800

James Joyce: I'm really forgetful. Does that count?

 

1132

02:17:49.360 --> 02:17:55.059

Rebecca Hale: Do you receive any government disability benefits of any kind? No.

 

1133

02:18:07.389 --> 02:18:11.029

Rebecca Hale: and you're not receiving any health insurance at this time. Right? Yes.

 

1134

02:18:16.549 --> 02:18:23.280

Rebecca Hale: Are you looking to? Apply for college, or would you be interested in getting help with the Fafsa application?

 

1135

02:18:23.670 --> 02:18:27.789

James Joyce: No, no. college is not for me.

 

1136

02:18:33.379 --> 02:18:35.539

Rebecca Hale: and there are no children in the household. Correct?

 

1137

02:18:35.620 --> 02:18:37.450

James Joyce: No?

 

1138

02:18:38.799 --> 02:18:42.009

James Joyce: Well. I mean so like

 

1139

02:18:42.350 --> 02:18:50.159

Rebecca Hale: my girlfriend. I don't have children, but, like my girlfriend has children, and like sometimes she stays over and like when she stays over like

 

1140

02:18:50.600 --> 02:18:52.449

James Joyce: I mean, her kid stays with us.

 

1141

02:18:52.920 --> 02:18:53.719

Rebecca Hale: Okay.

 

1142

02:18:53.879 --> 02:19:00.409

Rebecca Hale: but you're not. You're not like legally responsible for any children. Is that correct? And you don't have any children that live with you full time?

 

1143

02:19:00.620 --> 02:19:06.000

James Joyce: No, I mean my girlfriend wants me to be responsible. But no.

 

1144

02:19:13.520 --> 02:19:14.610

Rebecca Hale: and alright.

 

1145

02:19:15.790 --> 02:19:19.039

Rebecca Hale: thank you for your patience. I'm just getting set up here.

 

1146

02:19:19.760 --> 02:19:22.510

James Joyce: Sorry I don't have anything today. I'm off.

 

1147

02:19:25.730 --> 02:19:32.690

Rebecca Hale: So you said you don't have any health insurance at this time. Do you pay for any prescriptions? No.

 

1148

02:19:36.850 --> 02:19:37.860

Rebecca Hale: alright!

 

1149

02:19:42.799 --> 02:19:47.830

Rebecca Hale: And is your monthly household income less than $298.

 

1150

02:19:48.260 --> 02:19:58.169

Rebecca Hale: So again, I know I keep asking this. But like so when you say household like, we're just talking about me. Right? Okay? So yeah, now, II make more than that.

 

1151

02:20:01.720 --> 02:20:08.590

James Joyce: Sorry. I just get really confused because I'm like, I live in a house. And there's like people here. And I'm like, what is the household? I don't. Wanna. I don't wanna lie on anything.

 

1152

02:20:08.670 --> 02:20:30.069

Rebecca Hale: No, yeah. The the the questions tend to be framed around household because we're looking at a bunch of different benefits. And some of them look at people that you're living with. But we've already closed those out. There's other benefits. That look at just you, but they tend to think about like a household, even a household of one. They call it a household instead of just saying.

 

1153

02:20:30.220 --> 02:20:31.450

James Joyce: Okay.

 

1154

02:21:08.590 --> 02:21:09.370

Rebecca Hale: right

 

1155

02:21:11.230 --> 02:21:26.330

Rebecca Hale: now, are you currently receiving any SSI or supplemental Security income benefits? No, I don't think so. And you said you're not enrolled in Medicaid, and you don't have any health insurance. Correct? No.

 

1156

02:21:30.440 --> 02:21:34.030

Rebecca Hale: Have you lost any of your insurance in the last 90 days

 

1157

02:21:34.470 --> 02:21:35.220

James Joyce: now.

 

1158

02:21:35.400 --> 02:21:36.600

no, okay.

 

1159

02:21:39.280 --> 02:21:47.360

Rebecca Hale: Do you have a medical condition or chronic condition, or an ongoing special healthcare need, or an ongoing medication prescribed by a doctor?

 

1160

02:21:47.700 --> 02:21:49.710

James Joyce: No.

 

1161

02:21:50.260 --> 02:21:52.719

Rebecca Hale: Are you taking any college courses at this time?

 

1162

02:21:53.220 --> 02:21:55.330

James Joyce: No, definitely not.

 

1163

02:21:55.510 --> 02:21:57.709

Rebecca Hale: Do you have any Federal student loans

 

1164

02:21:57.820 --> 02:21:58.660

James Joyce: now?

 

1165

02:22:00.200 --> 02:22:01.739

Rebecca Hale: Are you a us citizen?

 

1166

02:22:01.860 --> 02:22:02.950

James Joyce: Yes.

 

1167

02:22:04.140 --> 02:22:09.280

Rebecca Hale: were you in foster care Foster? Care at age 18 or older?

 

1168

02:22:09.450 --> 02:22:10.230

James Joyce: No.

 

1169

02:22:17.990 --> 02:22:28.200

Rebecca Hale: alright. Now, I'm just gonna confirm some of your information. Can you just spell out your first and last name again for me, please. It's James JAME. S.

 

1170

02:22:28.270 --> 02:22:29.899

Rebecca Hale: Joyce.

 

1171

02:22:30.000 --> 02:22:36.120

James Joyce: JOYC. E. Do you have a middle initial, no.

 

1172

02:22:36.330 --> 02:22:38.419

Rebecca Hale: And are you a senior or a junior?

 

1173

02:22:39.390 --> 02:22:40.140

James Joyce: No?

 

1174

02:22:40.270 --> 02:22:44.269

Rebecca Hale: Oh, okay. And what is your legal sex, male or female?

 

1175

02:22:44.530 --> 02:22:47.019

Rebecca Hale: Okay, what is your current marital status

 

1176

02:22:47.040 --> 02:22:48.130

James Joyce: divorced.

 

1177

02:22:50.540 --> 02:22:52.079

Rebecca Hale: And what is your date of birth?

 

1178

02:22:52.600 --> 02:22:55.880

It's like February twelfth.

 

1179

02:22:56.900 --> 02:22:58.620

James Joyce: 1982.

 

1180

02:22:59.050 --> 02:22:59.750

Rebecca Hale: Okay.

 

1181

02:23:00.540 --> 02:23:02.349

James Joyce: sorry, 1986,

 

1182

02:23:03.640 --> 02:23:05.530

James Joyce: maybe 1987.

 

1183

02:23:07.270 --> 02:23:09.840

James Joyce: Somewhere. That makes me 36, I think, is what I said.

 

1184

02:23:09.890 --> 02:23:12.739

Rebecca Hale: yeah, you're 88.

 

1185

02:23:13.030 --> 02:23:19.630

Rebecca Hale: And what does your race are ethnicity? Are you white or Caucasian, black or African, American, American, Indian, Alaskan, Hawaiian.

 

1186

02:23:19.810 --> 02:23:22.039

James Joyce: I don't know. I'm a mix of stuff.

 

1187

02:23:23.920 --> 02:23:25.910

James Joyce: I don't really ask my mom that question.

 

1188

02:23:25.990 --> 02:23:29.380

Rebecca Hale: Okay, are you of a Hispanic or Latin origin.

 

1189

02:23:30.540 --> 02:23:32.420

James Joyce: Not, as far as I know.

 

1190

02:23:33.490 --> 02:23:38.560

Rebecca Hale: I thought about doing one of those 23 and me's isn't that one of those things?

 

1191

02:23:38.690 --> 02:23:40.080

James Joyce: I mean, maybe, that

 

1192

02:23:40.440 --> 02:23:42.989

Rebecca Hale: if I do that I'll let you know

 

1193

02:23:46.610 --> 02:23:58.430

Rebecca Hale: it's not necessary for the application we just collected. Is there anything you can help me to do? A 23. And me I don't think we have any access to that. But like or any referrals for that.

 

1194

02:23:58.890 --> 02:24:06.880

Rebecca Hale: But you should be able to find it online. If you're looking. we won't be able to help like offset the cost or anything like that. No.

 

1195

02:24:07.250 --> 02:24:09.220

Rebecca Hale: alright.

 

1196

02:24:10.580 --> 02:24:11.240

yes.

 

1197

02:24:14.850 --> 02:24:25.039

James Joyce: yeah. I've heard like, if you have certain something or another like you can get other cool things. So maybe I'll do that and see if there's things I qualify for.

 

1198

02:24:26.560 --> 02:24:27.260

Okay.

 

1199

02:24:27.450 --> 02:24:32.170

Rebecca Hale: did you live in the Us. For less than half the year last year?

 

1200

02:24:33.690 --> 02:24:45.540

Rebecca Hale:  did you live in the

 

1201

02:24:47.220 --> 02:24:49.640

James Joyce: I mean, I went to Canada for like a week.

 

1202

02:24:50.090 --> 02:24:55.539

Rebecca Hale: Okay, that's fun. It wasn't. Oh, I'm sorry to hear that.

 

1203

02:25:00.240 --> 02:25:05.300

Rebecca Hale: Alright. Now, did you receive any income from employment last year

 

1204

02:25:06.340 --> 02:25:08.430

Rebecca Hale: last year? Yes.

 

1205

02:25:08.770 --> 02:25:10.050

James Joyce: yeah.

 

1206

02:25:11.350 --> 02:25:13.369

James Joyce: Why do you need to know about last year?

 

1207

02:25:13.820 --> 02:25:21.570

Rebecca Hale: There's a specific benefit that is a tax credit that. Factors in your income from last year?

 

1208

02:25:22.780 --> 02:25:24.159

Rebecca Hale: Are you currently working?

 

1209

02:25:24.790 --> 02:25:31.469

James Joyce: Yes. I mean, not like at this exact moment. I'm talking to you at this exact moment. But like, I have a job.

 

1210

02:25:31.620 --> 02:25:37.220

Rebecca Hale: Okay, you have a job and you're currently receiving. Okay? So you receive a paycheck.

 

1211

02:25:37.600 --> 02:25:39.230

Rebecca Hale: Yes, okay.

 

1212

02:25:41.460 --> 02:25:53.120

Rebecca Hale: Have you lost a job? Or had your hours significantly reduced? Are you planning on starting another job in the next 30 days? No, okay.

 

1213

02:25:54.680 --> 02:25:55.860

Rebecca Hale: alright.

 

1214

02:26:04.870 --> 02:26:07.829

Rebecca Hale: alright. So we're gonna talk a little bit about your work income?

 

1215

02:26:08.060 --> 02:26:12.560

Rebecca Hale: How many hours a a week do you work?

 

1216

02:26:13.110 --> 02:26:15.600

James Joyce: I mean 30, if they'll let me.

 

1217

02:26:15.740 --> 02:26:17.380

Rebecca Hale: 30. Okay, yes.

 

1218

02:26:17.950 --> 02:26:20.689

James Joyce: But I mean, I usually end up with about 25.

 

1219

02:26:21.010 --> 02:26:25.299

Rebecca Hale: Okay. so we'll split the difference and put 28. How does that sound?

 

1220

02:26:25.680 --> 02:26:29.929

Rebecca Hale: I mean, it's fine with me. And what is your hourly rate.

 

1221

02:26:30.070 --> 02:26:33.110

James Joyce: 1275.

 

1222

02:26:35.590 --> 02:26:40.009

Rebecca Hale: Are you paid every week or every 2 weeks every week?

 

1223

02:26:49.670 --> 02:26:52.820

Rebecca Hale: I'm just gonna do some math. 1 s.

 

1224

02:27:04.160 --> 02:27:13.929

James Joyce: Oh, wait. Sorry. So I have 2 jobs. Did you want both of them like combined cause? If I combine the hours of both of them, I'm probably like 44 h.

 

1225

02:27:14.470 --> 02:27:21.420

Rebecca Hale: we could go one at a time. So I'll do this first job and then we'll talk about the next job. Oh, okay, that's fine.

 

1226

02:27:23.050 --> 02:27:25.969

Rebecca Hale: So this first job, where is that?

 

1227

02:27:26.260 --> 02:27:31.050

James Joyce:  Walmart? Walmart? Okay.

 

1228

02:27:31.260 --> 02:27:38.529

Rebecca Hale: And before taxes are getting paid taken out, is it? Do you receive about 3 57 a week in your paycheck?

 

1229

02:27:39.670 --> 02:27:58.030

James Joyce: I don't even know. That sounds yeah, sure. Yeah. So what I did was, I took the hours that you work a week, which is about 28, and I multiply that by your hourly rate, and came up with 357. Yeah, I mean, they. I just deposited into the bank. And then I don't. Yeah, that sounds right.

 

1230

02:27:58.350 --> 02:28:01.790

Rebecca Hale: You seem to know what you're talking about. So.

 

1231

02:28:01.970 --> 02:28:06.289

Rebecca Hale: And have you been working out that job? How long have you been working at Walmart.

 

1232

02:28:09.400 --> 02:28:11.500

James Joyce: I don't know, like 10 years.

 

1233

02:28:11.890 --> 02:28:14.960

Rebecca Hale: 10 years

 

1234

02:28:16.990 --> 02:28:19.840

Rebecca Hale: time flies doesn't it it does

 

1235

02:28:19.990 --> 02:28:23.890

Rebecca Hale:  and when was the last time, you repaired

 

1236

02:28:25.070 --> 02:28:30.929

Rebecca Hale: last week last week. Okay, yeah, I think it was last Friday. So the eighth

 

1237

02:28:32.210 --> 02:28:34.669

Rebecca Hale: yeah.

 

1238

02:28:36.450 --> 02:28:41.590

James Joyce: Oh, actually, I yeah, I need to go. I don't think I can.

 

1239

02:28:43.330 --> 02:28:49.050

James Joyce: Sorry I have an appointment I forgot about. Is there any chance like? Can I get the rental assistance

 

1240

02:28:49.100 --> 02:28:53.460

Rebecca Hale: like what's going on with that? Yep, I can give you a referral for that. Give me 1 s

 

1241

02:28:56.560 --> 02:28:57.760

Rebecca Hale: alright.

 

1242

02:28:58.930 --> 02:29:02.959

James Joyce: I mean, you're real nice. But like this is, I just need this.

 

1243

02:29:03.390 --> 02:29:08.750

Rebecca Hale: No, I completely understand. So let me see. Alright. You're living in Philadelphia.

 

1244

02:29:14.030 --> 02:29:14.720

and

 

1245

02:29:33.790 --> 02:29:39.230

Rebecca Hale: I'm trying to find the best program that works for you. So give me 1 s.

 

1246

02:29:45.080 --> 02:29:52.310

Rebecca Hale: Now I know you're receiving. You're kind of getting pressure from your landlord. Have you gotten any eviction notice, or like any threats of evicting?

 

1247

02:29:52.540 --> 02:29:54.799

Rebecca Hale: I mean definite threats.

 

1248

02:29:56.070 --> 02:30:07.550

Rebecca Hale: Me says that almost every time I walk in the door

 

1249

02:30:07.640 --> 02:30:09.300

Rebecca Hale: family centre.

 

1250

02:30:11.430 --> 02:30:12.330

James Joyce: Okay.

 

1251

02:30:12.440 --> 02:30:16.800

Rebecca Hale: okay. And their phone number is 2, 1, 5,

 

1252

02:30:18.050 --> 02:30:20.079

Rebecca Hale: 6, 8, 6,

 

1253

02:30:21.370 --> 02:30:23.800

Rebecca Hale: 7, 1, 5 0.

 

1254

02:30:26.040 --> 02:30:29.750

Rebecca Hale: And they're on 1430, Cherry Street.

 

1255

02:30:30.470 --> 02:30:33.130

James Joyce: Okay. what are their hours?

 

1256

02:30:33.870 --> 02:30:44.830

Rebecca Hale: Their hours are from 7 Am. To 5 pm. And then I'm gonna try to see if I have some other.

 

1257

02:30:46.800 --> 02:30:47.610

Rebecca Hale: Hmm.

 

1258

02:30:54.780 --> 02:31:04.679

Rebecca Hale: do alright. I'm also gonna give you the phone number for an organization called Turn, which is the Tenant Union representative network?

 

1259

02:31:05.630 --> 02:31:10.039

James Joyce: Oh, yeah, I know them. Yeah. I already talked to them.

 

1260

02:31:10.530 --> 02:31:12.079

Rebecca Hale: Were they helpful for you?

 

1261

02:31:12.390 --> 02:31:13.300

James Joyce: No.

 

1262

02:31:13.450 --> 02:31:18.349

Rebecca Hale: Oh, I'm sorry to hear that they said they didn't have any. They didn't have any funding

 

1263

02:31:22.200 --> 02:31:25.520

Rebecca Hale: alright. And we also have the phone number for HUD

 

1264

02:31:25.930 --> 02:31:40.659

Rebecca Hale: as well. There are very extensive waiting lists for HUD, though. So I just kind of want to prepare you that they might not be able to give you any like immediate assistance. Okay, gotcha.

 

1265

02:31:40.780 --> 02:31:46.919

Rebecca Hale: So I mean, I guess this apple tree sounds like, I haven't tried them yet. So I can definitely give them a try.

 

1266

02:31:48.010 --> 02:32:01.629

Rebecca Hale: And yeah, a lot of the other services that we have. We're like for people who are like actively homeless or like definitively gonna get kicked out. So

 

1267

02:32:01.920 --> 02:32:06.349

Rebecca Hale: there's also the Pennsylvania affordable apartment locator.

 

1268

02:32:06.400 --> 02:32:17.710

Rebecca Hale: If you do have to move this can be a really good resource for you. I have their phone number as well.

 

1269

02:32:19.350 --> 02:32:21.090

Rebecca Hale: 4 to 8,

 

1270

02:32:22.110 --> 02:32:23.669

Rebecca Hale: 8, 8, 4, 4.

 

1271

02:32:23.850 --> 02:32:25.320

James Joyce: Okay, thanks.

 

1272

02:32:25.650 --> 02:32:26.560

Rebecca Hale: Alright.

 

1273

02:32:28.890 --> 02:32:47.039

Rebecca Hale: And if you face any issues, you could definitely give us a call, or if you need any assistance with your snap like, if you need to reapply or if you want to finish that app like that screening for medicaid because if you need any help with your like health insurance, that's a good way to potentially provide you with that assistance.

 

1274

02:32:47.080 --> 02:32:49.180

James Joyce: Alright, yeah. Well, I'll call back.

 

1275

02:32:49.430 --> 02:32:50.270

Rebecca Hale: Okay.

 

1276

02:32:50.550 --> 02:32:55.940

Rebecca Hale: thank you so much, Mr. Joyce. Hope we have a wonderful rest of your day. Good luck!


"""

prompt = """
You are a helpful AI assistant who will summarize this transcript {transcript}, using the following template:
---------------------
Caller Information (Name, contact information, availability, household information)

Reason/Type of Call (Applying for benefits, Follow-Ups)

Previous Benefits History (Applied for, Receives, Denied, etc)

Put # in front of the benefit discussed (i.e. #SNAP, LIHEAP)

Discussion Points (Key information points)

Documents Needed (Income, Housing, etc)

Next Steps for Client

Next Steps for Agent
---------------------

"""

print("""
      Select an llm
      1. openhermes (default)
      2. dolphin
      3. gemini
      4. gpt 3.5
      5. gpt 4
      """)


llm = input() or "1"
prompt_template = PromptTemplate.from_template(prompt)
formatted_prompt= prompt_template.format(transcript=transcript)

if llm == "2":
    test = ollama_client(model_name="dolphin-mistral", prompt=formatted_prompt)
    print("""----------
        Dolphin
        """)
if llm == "3":
    test= google_gemini_client(prompt=formatted_prompt).text
    print("""----------
        Gemini
        """)
if llm == "4":
    print("""----------
      GPT 3.5
      """)
    test = gpt3_5(prompt=formatted_prompt)
if llm == "5":
    print("""----------
        GPT 4
        """)
    test = gpt_4_turbo(prompt=formatted_prompt)
else:
    test = ollama_client(model_name="openhermes", prompt=formatted_prompt)
    print("""
        Openhermes
        """)

print(test)
