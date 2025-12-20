import { AnswerElement, TemplateElementModel } from "../model/templateElement";

class WeightToScoreManager {
  currentWeightsSum: number;
  initialWeightsSum: number;
  maxScore: number;

  constructor(elements: TemplateElementModel[], maxScore: number) {
    const weight = this.calcTotalWeight(elements);
    this.currentWeightsSum = weight;
    this.initialWeightsSum = weight;
    this.maxScore = maxScore;
  }

  public calcFinalScore(currentWeight: number) {
    return (
      (this.currentWeightsSum > 0
        ? currentWeight / this.currentWeightsSum
        : 0) * this.maxScore
    ).toFixed(2);
  }

  public changeWeightsSum(diff: number) {
    this.currentWeightsSum += diff;
  }

  public reset() {
    this.currentWeightsSum = this.initialWeightsSum;
  }

  private calcTotalWeight(elements: TemplateElementModel[], totalWeight = 0) {
    elements.forEach((element) => {
      if (element.type === "answer") {
        totalWeight += (element as AnswerElement).properties.weight;
      }
      if (Array.isArray(element.properties.data)) {
        totalWeight += this.calcTotalWeight(element.properties.data);
      }
    });
    return totalWeight;
  }
}

export default WeightToScoreManager;
