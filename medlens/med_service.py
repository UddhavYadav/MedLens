import modal 
from modal import Image

appp=modal.App(name="clinical-assistant")
image=Image.debian_slim().pip_install("torch", "transformers", "accelerate","pillow")
secrets=[modal.Secret.from_name("huggingface-secret")]
GPU="T4"
MODAL_NAME="google/medgemma-1.5-4b-it"
pipe=None

@appp.function(image=image,gpu=GPU,secrets=secrets,timeout=1800)
def generate(payload:dict)->str:
    from PIL import Image
    import io
    import copy

    messages=payload["messages"]
    mode = payload.get("mode", "chat")
    print("typee of messages: ",type(messages))
    print("The status of upload in Modal",payload["upload"])
    # print("message before loop :",messages)
    if payload["upload"]:
        print("now it is inside at least if block")
        for item in messages[-1]["content"]:
            # print("the item in loop: ",item)
            if item["type"] == "image":
                item["image"] =  Image.open(io.BytesIO(item["image"]))
                print("this is inside if of modal")
                # debug code below
                print(type(item["image"]))
    print("the message is below:")
    print(messages)

    global pipe
    if pipe is None:
        from transformers import pipeline
        import torch
        pipe=pipeline(
            "image-text-to-text",
            model="google/medgemma-1.5-4b-it",
            torch_dtype=torch.bfloat16,
            device="cuda"
        )
    # output = pipe(text=messages, max_new_tokens=2000)
    if mode == "summary":
        output = pipe(
            text=messages,
            max_new_tokens=300,
            do_sample=False,
            temperature=0.0,
            repetition_penalty=1.2,
        )

    elif mode == "chat":
        output = pipe(
            text=messages,
            max_new_tokens=800,       # more space for chat
            do_sample=True,           # allow natural tone
            temperature=0.7,
            repetition_penalty=1.1,
        )
    raw_content= output[0]["generated_text"][-1]["content"]
    if "<unused95>" in raw_content:
        clean_content = raw_content.split("<unused95>")[-1].strip()
        return clean_content
    return raw_content
    # return "hello from modal"
