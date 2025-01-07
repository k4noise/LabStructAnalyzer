import React, { Suspense, useEffect, useState } from "react";
import { Outlet, useNavigation } from "react-router";
import Spinner from "../Spinner";
import Nav from "../Nav/Nav";

const BaseLayout: React.FC<{ delay: number }> = ({ delay }) => {
  const navigation = useNavigation();
  const [showSpinner, setShowSpinner] = useState(false);

  useEffect(() => {
    let timer;
    if (navigation.state === "loading") {
      timer = setTimeout(() => {
        setShowSpinner(true);
      }, delay);
    } else {
      setShowSpinner(false);
      clearTimeout(timer);
    }

    return () => clearTimeout(timer);
  }, [navigation.state]);

  return (
    <>
      <Suspense fallback={<Spinner />}>
        <Nav />
      </Suspense>
      <div>
        {showSpinner ? (
          <Spinner />
        ) : (
          <Suspense fallback={<Spinner />}>
            <Outlet />
          </Suspense>
        )}
      </div>
    </>
  );
};

export default BaseLayout;
