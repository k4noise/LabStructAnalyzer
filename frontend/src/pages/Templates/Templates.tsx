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
    const template = formData.get("template");
    if (template && template["name"] == "") return;
    const { data, error, description } = await sendTemplate(formData);
    if (error) {
      navigate(`/error?code=${error}&description=${description}`);
    }
    if (data) {
      localStorage.setItem("pageData", JSON.stringify(data));
      navigate("/template");
    }
  };

  return (
    <div>
      <h2 className="text-3xl font-medium text-center mb-10">
        Отчеты лабораторных работ курса "{courseName}"
      </h2>
      <button
        className="text-l p-4 rounded-xl underline mb-5"
        onClick={handleOpen}
      >
        + Добавить новый шаблон
      </button>
      <Modal isOpen={isOpen} onClose={handleClose}>
        <form onSubmit={handleUploadTemplate}>
          <h3 className="text-xl font-medium text-center mb-3">
            Шаблон для импорта
          </h3>
          <p className="text-l text-center mb-8">
            Поддерживаемые форматы: docx
          </p>
          <input type="file" name="template" className="mb-8" />
          <button className="block px-2 py-1 ml-auto border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950">
            Загрузить
          </button>
        </form>
      </Modal>
      <p className="text-l">Нет шаблонов</p>
    </div>
  );
};

export default Templates;
