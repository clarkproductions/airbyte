import { AirbyteRequestService } from "core/request/AirbyteRequestService";
import { Operation } from "./operation";
import Status from "core/statuses";

class OperationService extends AirbyteRequestService {
  get url() {
    return "operations";
  }

  public async check(
    operation: Operation
  ): Promise<{ status: "succeeded" | "failed"; message: string }> {
    const rs = await this.fetch<{
      status: "succeeded" | "failed";
      message: string;
    }>(`${this.url}/check`, operation.operatorConfiguration);

    if (rs.status === Status.FAILED) {
      // TODO: place proper error
      throw new Error("failed");
    }

    return rs;
  }
}

export { OperationService };
