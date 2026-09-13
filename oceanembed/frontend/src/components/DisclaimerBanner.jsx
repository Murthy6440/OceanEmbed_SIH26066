import React from "react";

export default function DisclaimerBanner({ text }) {
  return (
    <div className="disclaimer-banner" role="note">
      <span className="disclaimer-icon">⚠️</span>
      <span>
        <b>Prototype notice —</b> {text}
      </span>
    </div>
  );
}
