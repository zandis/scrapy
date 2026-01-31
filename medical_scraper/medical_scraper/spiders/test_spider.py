"""Test spider to verify the scraping pipeline works correctly."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import scrapy

from medical_scraper.items import MedicalContentItem

if TYPE_CHECKING:
    from collections.abc import Iterator

    from scrapy.http import Response


class TestSpider(scrapy.Spider):
    """Test spider that generates sample items to verify the pipeline."""

    name = "test"

    # Use a simple allowed URL for testing
    start_urls = ["data:text/html,<html><body>Test</body></html>"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response: Response) -> Iterator[MedicalContentItem]:
        """Generate sample items to test the pipeline."""
        self.logger.info("Generating test items to verify pipeline...")

        # Sample MD Cafe item
        yield MedicalContentItem(
            url="https://md.cafe/cardiology/heart-failure",
            title="Heart Failure - Diagnosis and Treatment",
            source="md_cafe",
            category="Cardiology",
            subcategory="Heart Conditions",
            breadcrumbs=["Cardiology", "Heart Conditions", "Heart Failure"],
            last_updated="2024-01-15",
            content="""
Heart failure is a chronic condition where the heart doesn't pump blood as well as it should.

Symptoms:
- Shortness of breath during activity or when lying down
- Fatigue and weakness
- Swelling in legs, ankles, and feet
- Rapid or irregular heartbeat
- Reduced ability to exercise
- Persistent cough or wheezing

Diagnosis:
Heart failure is diagnosed through physical examination, blood tests,
electrocardiogram (ECG), echocardiogram, and stress tests.

Treatment:
Treatment typically includes medications (ACE inhibitors, beta-blockers,
diuretics), lifestyle changes, and in some cases, devices or surgery.

Prevention:
- Control high blood pressure
- Maintain healthy weight
- Exercise regularly
- Don't smoke
- Limit alcohol and sodium intake
            """.strip(),
            html_content="""
<article class="medical-content">
    <h1>Heart Failure - Diagnosis and Treatment</h1>
    <div class="breadcrumb">Cardiology > Heart Conditions > Heart Failure</div>
    <section>
        <h2>Overview</h2>
        <p>Heart failure is a chronic condition where the heart doesn't pump blood as well as it should.</p>
    </section>
    <section>
        <h2>Symptoms</h2>
        <ul>
            <li>Shortness of breath during activity or when lying down</li>
            <li>Fatigue and weakness</li>
            <li>Swelling in legs, ankles, and feet</li>
        </ul>
    </section>
</article>
            """.strip(),
        )

        # Sample MSD Manuals item
        yield MedicalContentItem(
            url="https://www.msdmanuals.com/professional/pulmonary-disorders/asthma",
            title="Asthma - Pulmonary Disorders",
            source="msdmanuals",
            category="Pulmonary Disorders",
            subcategory="Obstructive Airway Diseases",
            breadcrumbs=["Professional", "Pulmonary Disorders", "Obstructive Airway Diseases", "Asthma"],
            last_updated="2024-02-01",
            content="""
Asthma is a disease of diffuse airway inflammation caused by a variety of
triggering stimuli resulting in partially or completely reversible bronchoconstriction.

Etiology:
Asthma is a multifactorial disease. Genetic factors, allergies, and environmental
exposures all play roles in its development.

Pathophysiology:
The hallmarks of asthma are:
- Bronchoconstriction
- Airway edema
- Mucus hypersecretion
- Airway hyperresponsiveness

Symptoms and Signs:
- Wheezing
- Dyspnea
- Chest tightness
- Cough (often worse at night)

Diagnosis:
- Pulmonary function tests showing reversible obstruction
- Peak flow monitoring
- Bronchoprovocation testing when diagnosis uncertain

Treatment:
- Quick-relief medications: Short-acting beta-agonists
- Long-term control: Inhaled corticosteroids, LABAs, leukotriene modifiers
- Biologic therapies for severe asthma
            """.strip(),
            html_content="""
<article class="topic-content">
    <h1 class="topic-title">Asthma</h1>
    <nav aria-label="breadcrumb">
        <a href="#">Professional</a> > <a href="#">Pulmonary Disorders</a> > Asthma
    </nav>
    <section>
        <h2>Etiology</h2>
        <p>Asthma is a multifactorial disease involving genetic factors, allergies, and environmental exposures.</p>
    </section>
    <section>
        <h2>Treatment</h2>
        <p>Treatment includes quick-relief and long-term control medications.</p>
    </section>
</article>
            """.strip(),
        )

        # Additional test items
        yield MedicalContentItem(
            url="https://md.cafe/neurology/migraine",
            title="Migraine Headaches",
            source="md_cafe",
            category="Neurology",
            subcategory="Headache Disorders",
            breadcrumbs=["Neurology", "Headache Disorders", "Migraine"],
            content="""
Migraine is a neurological condition characterized by recurrent headaches
that are moderate to severe. Typically, they affect one half of the head,
are pulsating in nature, and can last from 2 to 72 hours.

Associated symptoms may include nausea, vomiting, and sensitivity to light,
sound, or smell. The pain is generally made worse by physical activity.

Treatment includes both acute therapy (triptans, NSAIDs) and preventive
measures (beta-blockers, anticonvulsants, CGRP inhibitors).
            """.strip(),
            html_content="<article><h1>Migraine Headaches</h1><p>Content here...</p></article>",
        )

        yield MedicalContentItem(
            url="https://www.msdmanuals.com/professional/infectious-diseases/bacterial-infections",
            title="Overview of Bacterial Infections",
            source="msdmanuals",
            category="Infectious Diseases",
            subcategory="Bacterial Infections",
            breadcrumbs=["Professional", "Infectious Diseases", "Bacterial Infections"],
            content="""
Bacteria are microscopic, single-celled organisms. They are among the
earliest known life forms on Earth. There are thousands of different
kinds of bacteria, and they live in every conceivable environment.

Pathogenic bacteria cause disease through various mechanisms including:
- Toxin production
- Direct tissue invasion
- Immune-mediated damage

Common bacterial infections include:
- Streptococcal infections
- Staphylococcal infections
- E. coli infections
- Pneumococcal infections

Treatment typically involves antibiotics selected based on culture
and sensitivity testing when possible.
            """.strip(),
            html_content="<article><h1>Bacterial Infections</h1><p>Overview content...</p></article>",
        )

        self.logger.info("Generated 4 test items successfully")
