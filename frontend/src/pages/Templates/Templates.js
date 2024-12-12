import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useNavigate, useSearchParams } from "react-router";
import Modal from "../../components/Modal/Modal";
import { useState } from "react";
import { sendTemplate } from "../../actions/sendTemplate";
const Templates = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const courseName = searchParams.get("course");
    const [isOpen, setIsOpen] = useState(false);
    const handleOpen = () => {
        setIsOpen(true);
    };
    const handleClose = () => {
        setIsOpen(false);
    };
    const handleUploadTemplate = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        if (formData.get("template")?.name == "")
            return;
        const { data } = await sendTemplate(formData);
        if (data) {
            localStorage.setItem("pageData", JSON.stringify(data));
            navigate("/template");
        }
    };
    return (_jsxs("div", { children: [_jsxs("h2", { className: "text-3xl font-medium text-center mb-10", children: ["\u041E\u0442\u0447\u0435\u0442\u044B \u043B\u0430\u0431\u043E\u0440\u0430\u0442\u043E\u0440\u043D\u044B\u0445 \u0440\u0430\u0431\u043E\u0442 \u043A\u0443\u0440\u0441\u0430 \"", courseName, "\""] }), _jsx("button", { className: "text-l p-4 rounded-xl underline mb-5", onClick: handleOpen, children: "+ \u0414\u043E\u0431\u0430\u0432\u0438\u0442\u044C \u043D\u043E\u0432\u044B\u0439 \u0448\u0430\u0431\u043B\u043E\u043D" }), _jsx(Modal, { isOpen: isOpen, onClose: handleClose, children: _jsxs("form", { onSubmit: handleUploadTemplate, children: [_jsx("h3", { className: "text-xl font-medium text-center mb-3", children: "\u0428\u0430\u0431\u043B\u043E\u043D \u0434\u043B\u044F \u0438\u043C\u043F\u043E\u0440\u0442\u0430" }), _jsx("p", { className: "text-l text-center mb-8", children: "\u041F\u043E\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u043C\u044B\u0435 \u0444\u043E\u0440\u043C\u0430\u0442\u044B: docx" }), _jsx("input", { type: "file", name: "template", className: "mb-8" }), _jsx("button", { className: "block px-2 py-1 ml-auto border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950", children: "\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044C" })] }) }), _jsx("p", { className: "text-l", children: "\u041D\u0435\u0442 \u0448\u0430\u0431\u043B\u043E\u043D\u043E\u0432" })] }));
};
export default Templates;
