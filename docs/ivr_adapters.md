# Kisan Mitra AI — Production Telephony & IVR Webhook Adapters

This document details the configuration layouts and webhook adapter templates to wire Kisan Mitra AI's telephony engine with production IVR carriers.

---

## 1. Webhook Handoff Architecture

```
┌───────────┐                ┌──────────────────┐                ┌─────────────────┐
│  Farmer   │ ──(Voice/SIP)─►│   IVR Carrier    │ ──(HTTP POST)─►│  Kisan Mitra    │
│  Handset  │ ◄──(TwiML/Audio)│ (Twilio/Exotel)  │ ◄──(XML/JSON)──│  Call Manager   |
└───────────┘                └──────────────────┘                └─────────────────┘
```

1. **Incoming Call**: The carrier intercepts the SIP invite and triggers the registered webhook.
2. **State Processing**: Kisan Mitra resolves the DTMF digit, updates the call session, and responds with immediate instructions.
3. **Execution**: The carrier plays TTS or captures digits based on the instructions.

---

## 2. Twilio Voice Adapter (TwiML)

### Webhook URL configuration
- In Twilio Console: Set **Voice Request URL** to: `https://api.kisanmitra.in/api/v1/telephony/twilio/webhook`
- Method: `POST`

### TwiML Response Snippets
The backend formats standard TwiML XML payloads to direct the Twilio voice agent:

#### Language Selection (GREETING state)
```xml
<Response>
    <Gather numDigits="1" action="/api/v1/telephony/twilio/webhook" method="POST" timeout="5">
        <Speak voice="Polly.Aditi" language="hi-IN">
            किसान मित्र में स्वागत है। हिंदी के लिए एक दबाएं। Press two for English.
        </Speak>
    </Gather>
    <Redirect>/api/v1/telephony/twilio/webhook?digits=timeout</Redirect>
</Response>
```

#### Scheme Inquiry Voice Readback
```xml
<Response>
    <Speak voice="Polly.Aditi" language="hi-IN">
        जांच करने पर, आप पीएम-किसान योजना के लिए पात्र हैं। 
        इसमें आपको प्रति वर्ष 6000 रुपये मिलते हैं। 
        आवेदन के लिए आपके पास आधार कार्ड होना आवश्यक है।
    </Speak>
    <Gather numDigits="1" action="/api/v1/telephony/twilio/webhook" method="POST" timeout="5">
        <Speak voice="Polly.Aditi" language="hi-IN">
            मुख्य मेनू पर वापस जाने के लिए 9 दबाएं।
        </Speak>
    </Gather>
</Response>
```

---

## 3. Exotel Webhook Passthrough Schema

- Webhook Configuration: In Exotel Flow Builder, link an HTTP applet pointing to: `https://api.kisanmitra.in/api/v1/telephony/exotel/passthrough`

### Payload Parameters Sent by Exotel
Exotel sends the following query string params to our backend:
- `CallSid`: Unique Exotel call session ID
- `From`: Caller's phone number
- `Digits`: DTMF digit pressed by the farmer
- `Status`: Current state (`connected`, `completed`)

### Backend JSON Response Format
```json
{
  "status": "success",
  "response": {
    "action": "gather",
    "play_text": "पीएम-किसान योजना के लिए पात्र होने के लिए 1 दबाएं।",
    "voice": "female_hindi",
    "num_digits": 1,
    "timeout": 4
  }
}
```

---

## 4. Airtel IQ SIP trunk Integration

For enterprise hosting utilizing direct VoIP gateways (Airtel IQ SIP trunk):

### SIP Gateway Trunk Mapping
Ensure the backend Asterisk or FreeSWITCH server maps the SIP registration details:

```text
[airtel-iq-trunk]
type=peer
host=10.230.12.44               ; Airtel SIP IP
port=5060
dtmfmode=rfc2833                ; Standard in-band DTMF detection
disallow=all
allow=ulaw                      ; Voice codecs
allow=alaw                      ; Low latency high fidelity audio
context=kisan-mitra-inbound
```

### Inbound Asterisk Dialplan Routing (`extensions.conf`)
```text
[kisan-mitra-inbound]
exten => s,1,NoOp(Incoming Airtel Call)
 same => n,Answer()
 same => n,AGI(agi://localhost:4573/ivr_handler) ; Pipes RTP stream to our speech-recognition / AGI server
 same => n,Hangup()
```
