import { useEffect, useRef } from "react";
import EditorJS, { OutputData } from "@editorjs/editorjs";
import Paragraph from "@editorjs/paragraph";
import ImageTool from "@editorjs/image";
import List from "@editorjs/list";
import CodeTool from "@editorjs/code";
import { api } from "../../utils/sendRequest";

export interface EditorProps {
  initialData?: OutputData | null;
  onChange?: (data: OutputData) => void;
  fieldName?: string;
  register?: (name: string, options?: any) => void;
  setValue?: (name: string, data: OutputData, opts?: any) => void;
  readOnly?: boolean;
}

export default function Editor({
  initialData = null,
  onChange,
  fieldName,
  register,
  setValue,
  readOnly = false,
}: EditorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<EditorJS>();
  const isInitialized = useRef(false);
  const previousBlocksRef = useRef<any[]>([]);

  async function uploadImage(file: File): Promise<string> {
    try {
      const form = new FormData();
      form.append("file", file);

      const response = await fetch("/images/upload", {
        method: "POST",
        body: form,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const { url } = await response.json();
      return "/" + url;
    } catch (error) {
      console.error("Image upload failed:", error);
      throw error;
    }
  }

  async function deleteImage(url: string): Promise<void> {
    return await api.delete(`/images/${url}`);
  }

  async function handlePaste(evt: ClipboardEvent) {
    const file = evt.clipboardData?.files?.[0];
    if (!file || !file.type.startsWith("image/")) return;

    evt.preventDefault();

    try {
      const url = await uploadImage(file);
      await instanceRef.current!.blocks.insert("image", { file: { url } });

      const last = instanceRef.current!.blocks.getBlocksCount() - 1;
      instanceRef.current!.caret.setToBlock(last, "end");
    } catch (error) {
      console.error("Failed to paste image:", error);
    }
  }

  async function checkForDeletedImages(currentBlocks: any[]) {
    const currentImageUrls = new Set(
      currentBlocks
        .filter((block) => block.type === "image" && block.data?.file?.url)
        .map((block) => block.data.file.url)
    );

    const previousImageUrls = new Set(
      previousBlocksRef.current
        .filter((block) => block.type === "image" && block.data?.file?.url)
        .map((block) => block.data.file.url)
    );

    for (const url of previousImageUrls) {
      if (!currentImageUrls.has(url)) {
        await deleteImage(url.replace(/^\//, ""));
      }
    }

    previousBlocksRef.current = currentBlocks;
  }

  useEffect(() => {
    if (isInitialized.current || !containerRef.current) return;

    if (register && fieldName) register(fieldName);

    instanceRef.current = new EditorJS({
      holder: containerRef.current,
      autofocus: true,
      readOnly: readOnly,
      defaultBlock: "paragraph",
      placeholder: "Введите текст…",

      data: initialData ?? {
        blocks: [{ type: "paragraph", data: { text: "" } }],
      },

      tools: {
        paragraph: { class: Paragraph, inlineToolbar: ["bold", "italic"] },
        image: {
          class: ImageTool,
          config: {
            uploader: {
              uploadByFile: async (file: File) => {
                try {
                  const url = await uploadImage(file);
                  return {
                    success: 1,
                    file: { url },
                  };
                } catch (error) {
                  return {
                    success: 0,
                    message: "Upload failed",
                  };
                }
              },
            },
          },
        },
        list: {
          class: List,
          inlineToolbar: true,
          config: {
            defaultStyle: "unordered",
          },
        },
        code: {
          class: CodeTool,
        },
      },

      onChange: async () => {
        try {
          const data = await instanceRef.current!.save();
          await checkForDeletedImages(data.blocks);

          if (setValue && fieldName) {
            setValue(fieldName, data, {
              shouldDirty: true,
              shouldValidate: true,
            });
          }

          onChange?.(data);
        } catch (error) {
          console.error("Failed to save editor data:", error);
        }
      },
    });

    instanceRef.current.isReady.then(async () => {
      try {
        const data = await instanceRef.current!.save();
        previousBlocksRef.current = data.blocks;
      } catch (error) {
        console.error("Failed to get initial blocks:", error);
      }
    });

    isInitialized.current = true;

    const container = containerRef.current;
    container.addEventListener("paste", handlePaste);

    return () => {
      container.removeEventListener("paste", handlePaste);

      if (instanceRef.current?.destroy) {
        instanceRef.current.isReady
          .then(() => {
            instanceRef.current?.destroy();
            instanceRef.current = undefined;
            isInitialized.current = false;
          })
          .catch(console.error);
      }
    };
  }, [fieldName, register, setValue, onChange]);

  return (
    <div
      className={`lsa-editor border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950 ${
        readOnly ? " lsa-editor-readonly" : ""
      }
        `}
      ref={containerRef}
    />
  );
}
