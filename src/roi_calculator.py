"""
FOOD PLANT AI - ROI Calculator Business Logic
"""

from typing import Dict, Any


def calculate_roi(
    monthly_batches: int,
    failure_rate_pct: float,
    loss_per_batch_inr: float,
    preventable_pct: float,
    initial_cost_inr: float,
    annual_maintenance_inr: float
) -> Dict[str, Any]:
    """
    Calculates AI-enabled ROI for spice quality management.
    
    Parameters
    ----------
    monthly_batches : int
        Total production batches per month
    failure_rate_pct : float
        Current quality failure rate percentage (e.g. 25.0 for 25%)
    loss_per_batch_inr : float
        Average financial loss per failed batch in INR
    preventable_pct : float
        Expected percentage of failures the AI system can prevent
    initial_cost_inr : float
        One-time development and deployment cost in INR
    annual_maintenance_inr : float
        Annual maintenance and operating cost in INR
    
    Returns
    -------
    dict with all computed financial metrics
    """
    # Monthly metrics
    monthly_failed = monthly_batches * (failure_rate_pct / 100)
    monthly_loss = monthly_failed * loss_per_batch_inr
    monthly_savings = monthly_loss * (preventable_pct / 100)

    # Annual metrics
    annual_savings = monthly_savings * 12
    annual_operating_cost = annual_maintenance_inr
    net_annual_benefit = annual_savings - annual_operating_cost

    # ROI (excludes initial cost from denominator to show ongoing returns)
    total_annual_cost = initial_cost_inr + annual_maintenance_inr
    roi_pct = (net_annual_benefit - 0) / max(total_annual_cost, 1) * 100

    # Payback period in months
    payback_months = initial_cost_inr / max(monthly_savings, 1)

    # 3-year projection (cumulative net benefit by end of each year)
    year1_net = annual_savings - annual_operating_cost - initial_cost_inr
    year2_net = year1_net + (annual_savings - annual_operating_cost)
    year3_net = year2_net + (annual_savings - annual_operating_cost)

    return {
        "monthly_batches": monthly_batches,
        "failure_rate_pct": failure_rate_pct,
        "monthly_failed_batches": round(monthly_failed, 1),
        "monthly_financial_loss_inr": round(monthly_loss, 0),
        "monthly_savings_inr": round(monthly_savings, 0),
        "annual_savings_inr": round(annual_savings, 0),
        "annual_operating_cost_inr": round(annual_operating_cost, 0),
        "net_annual_benefit_inr": round(net_annual_benefit, 0),
        "initial_cost_inr": round(initial_cost_inr, 0),
        "roi_percentage": round(roi_pct, 1),
        "payback_months": round(payback_months, 1),
        "year1_net_inr": round(year1_net, 0),
        "year2_net_inr": round(year2_net, 0),
        "year3_net_inr": round(year3_net, 0),
    }
